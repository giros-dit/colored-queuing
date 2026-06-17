// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * net/sched/sch_bfifo_cc.c BFIFO scheme with Color Packet Control.
 *
 * Authors:	Aitor Encinas Alonso, <aitor.encinas.alonso@alumnos.upm.es>
*/

#include <linux/module.h>
#include <linux/skbuff.h>
#include <linux/ip.h>
#include <linux/ipv6.h>
#include <linux/netdevice.h>
#include <linux/list.h>
#include <net/pkt_sched.h>
#include <net/inet_ecn.h>
#include <net/sch_generic.h>
#include <linux/tc_bfifo_cc.h>
#include <linux/tracepoint.h>
#include <linux/netlink.h>
#include <linux/slab.h>

struct bfifo_cc_sched_data {
	u32 ecn_count; // Number of packets with flag in the queue
	struct list_head ecn_list; // Internal List to store ecn_skb_nodes. A list_head stores pointers to the next and previous elements in the list, and the elements can not be skb because they'll corrupt the qdisc.
	spinlock_t lock; // Spinlock to protect the list from concurrent access
	u32 queue_control; 
	u32 deficit; // Deficit counter of the DRR parent class
	u32 tmax;
	u32 mode;
};

struct ecn_skb_node {
	struct sk_buff *skb; // Pointer to the packet (what we store) with flag
	struct list_head list; // Wrap the pointer of the skb into a list
};

#define SCH_bfifo_cc(sch) ((struct bfifo_cc_sched_data *)qdisc_priv(sch))

static struct kmem_cache *ecn_node_cache;

static inline int qdisc_enqueue_tail_bfifo_cc(struct sk_buff *skb, struct Qdisc *sch) {
	struct sk_buff *last = sch->q.tail;

	if (last) {
		skb->next = NULL;
		last->next = skb;
		skb->prev = last;
		sch->q.tail = skb;
	} else {
		sch->q.tail = skb;
		sch->q.head = skb;
	}

	sch->q.qlen++;
	qdisc_qstats_backlog_inc(sch, skb); // Increase the backlog
	return NET_XMIT_SUCCESS;
}

static inline struct sk_buff *qdisc_dequeue_head_bfifo_cc(struct Qdisc *sch) {
	struct sk_buff *skb = sch->q.head;

	if (likely(skb != NULL)) {
		sch->q.head = skb->next;
		sch->q.qlen--;
		if (sch->q.head == NULL)
			sch->q.tail = NULL;

		if (sch->q.head != NULL)
			skb->next->prev = NULL;
		skb->next = NULL;
	}

	if (likely(skb != NULL)) {
		qdisc_qstats_backlog_dec(sch, skb); // Decrease the backlog
		qdisc_bstats_update(sch, skb); // Update the backlog of the parent qdiscs
	}

	return skb;
}

/*
Extract the flag of the packet:
First, it looks if the Ethernet EtherType value is IP or IPv6.
Only if the packet is IP or IPv6, we extract the TOS value and see the fourth bit.
If the packet carries the flag value, the function returns true. Otherwise, returns false.
*/
static bool skb_has_ecn_ce(struct sk_buff *skb) {
	if (skb->protocol == htons(ETH_P_IP)) {
        struct iphdr *iph = ip_hdr(skb);
        return iph && ((iph->tos >> 2) & 0x04);
    } else if (skb->protocol == htons(ETH_P_IPV6)) {
        struct ipv6hdr *ip6h = ipv6_hdr(skb);
        return ip6h && ((ipv6_get_dsfield(ip6h) >> 2) & 0x04);
    }
    return false;
}

/*Dequeue and drop the flagged victim packet from the qdisc queue*/
static bool bfifo_cc_dequeue_for_drop(struct Qdisc *sch, struct sk_buff *ecn_victim, struct sk_buff **to_free) {

	if (ecn_victim->prev) {
		// If the victim is neither the first packet in the queue nor the last one
		if (ecn_victim->next) {
			ecn_victim->prev->next = ecn_victim->next;
			ecn_victim->next->prev = ecn_victim->prev;
		// If the victim is the last packet in the queue (i.e., the tail)
		} else {
			ecn_victim->prev->next = NULL;
			sch->q.tail = ecn_victim->prev;
		}
	} else {
		// if the victim is the first packet in the queue (i.e., the head)
		if (ecn_victim->next) {
			ecn_victim->next->prev = NULL;
			sch->q.head = ecn_victim->next;
		// If the victim is the only packet in the queue
		} else {
			sch->q.head = NULL;
			sch->q.tail = NULL;
		}
	}

	ecn_victim->next = NULL;
	ecn_victim->prev = NULL;
	sch->q.qlen--;
	qdisc_qstats_backlog_dec(sch, ecn_victim); // Decrease the backlog
	qdisc_tree_reduce_backlog(sch, 1, ecn_victim->len); // Decrease the backlog of the parent qdiscs
	qdisc_drop(ecn_victim, sch, to_free); // Drop the packet
	return true;
}

/*Enqueue or discard packets when arrive to the queue*/
static int bfifo_cc_enqueue(struct sk_buff *skb, struct Qdisc *sch,
			 struct sk_buff **to_free)
{
	struct bfifo_cc_sched_data *q = SCH_bfifo_cc(sch);
	bool has_ecn = skb_has_ecn_ce(skb);

	spin_lock_bh(&q->lock);
	unsigned int limit = READ_ONCE(sch->limit);
	u32 byte_qlen = READ_ONCE(sch->qstats.backlog);
	u32 queue_control = q->queue_control;
	u32 pkt_len = qdisc_pkt_len(skb);
	u32 threshold;

	if (unlikely(limit == 0)) {
		spin_unlock_bh(&q->lock);
		return qdisc_drop(skb, sch, to_free);
	}

	if (likely(byte_qlen + pkt_len <= limit)){
		if (q->mode == 1) {
			u32 rounded = DIV_ROUND_UP(q->deficit, q->tmax) * q->tmax;
			threshold = queue_control + rounded;
		} else {
			threshold = queue_control;
		}

		if (byte_qlen + pkt_len > threshold) {
			if (has_ecn) {
				spin_unlock_bh(&q->lock);
				return qdisc_drop(skb, sch, to_free);
			} else {
				u32 dropped_bytes = 0;
				while ((dropped_bytes < pkt_len) && (q->ecn_count > 0) && (q->mode == 1)) {
					struct ecn_skb_node *node = list_entry(q->ecn_list.prev, struct ecn_skb_node, list); // Get the last node in the list
					struct sk_buff *ecn_victim = node->skb; // Get the skb from the node
					if (!ecn_victim) 
						break; // If the node is empty, break the loop
					dropped_bytes += qdisc_pkt_len(ecn_victim); // Decrease the bytes to drop	
					list_del(&node->list); // Remove the node from the list
					q->ecn_count--;
					byte_qlen -= qdisc_pkt_len(ecn_victim); // Update the byte queue length
					bfifo_cc_dequeue_for_drop(sch, ecn_victim, to_free); // Drop the yellow packet from the qdisc queue
					kmem_cache_free(ecn_node_cache, node); // Free the node
				}
				int ret = qdisc_enqueue_tail_bfifo_cc(skb, sch);
				spin_unlock_bh(&q->lock); // Unlock the list
				return ret;
			}
		} else {
			if (has_ecn) {
				//Store the packet with flag in the internal queue
				struct ecn_skb_node *node = kmem_cache_alloc(ecn_node_cache, GFP_ATOMIC); // Allocate dynamic cache memory for the node
				if (node) {
					node->skb = skb;
					list_add_tail(&node->list, &q->ecn_list);
					q->ecn_count++;
				}
			} 
			int ret = qdisc_enqueue_tail_bfifo_cc(skb, sch);
			trace_printk("Queue length: %u\n", sch->q.qlen);
			spin_unlock_bh(&q->lock); // Unlock the list
			return ret;
		}
	}

	spin_unlock_bh(&q->lock); // Unlock the list
	/* If the queue is full and there are no flagged packets, drop the new packet */
	return qdisc_drop(skb, sch, to_free); // Drop the new packet
}

static struct sk_buff *bfifo_cc_dequeue(struct Qdisc *sch) {
	struct bfifo_cc_sched_data *q = SCH_bfifo_cc(sch);
	spin_lock_bh(&q->lock);
	struct sk_buff *skb = qdisc_dequeue_head_bfifo_cc(sch);

	if (skb && skb_has_ecn_ce(skb) && q->ecn_count > 0) {

		struct ecn_skb_node *node = list_entry(q->ecn_list.next, struct ecn_skb_node, list);
		if (node->skb == skb) {
			list_del(&node->list); // Remove the node from the list
			q->ecn_count--;
			kmem_cache_free(ecn_node_cache, node); // Free the node
		}
	}

	trace_printk("Queue length: %u\n", sch->q.qlen);
	spin_unlock_bh(&q->lock);
	return skb;
}

static void bfifo_cc_reset(struct Qdisc *sch) {
    struct bfifo_cc_sched_data *q = SCH_bfifo_cc(sch);
	struct ecn_skb_node *node, *tmp;

	spin_lock_bh(&q->lock);
	list_for_each_entry_safe(node, tmp, &q->ecn_list, list) {
		list_del(&node->list);
		kmem_cache_free(ecn_node_cache, node);
	}

	spin_unlock_bh(&q->lock);
	// Reset the qdisc queue
	q->ecn_count = 0;
	qdisc_reset_queue(sch);
}

static int bfifo_cc_init(struct Qdisc *sch, struct nlattr *opt, struct netlink_ext_ack *extack) {

	struct bfifo_cc_sched_data *q = SCH_bfifo_cc(sch);
	INIT_LIST_HEAD(&q->ecn_list);
	spin_lock_init(&q->lock); // Initialize the spinlock
	q->ecn_count = 0;
	q->queue_control = 0;
	q->deficit = 0;
	q->tmax = 1500;
	q->mode = 0;

	if (opt == NULL) {
        u32 limit = qdisc_dev(sch)->tx_queue_len * psched_mtu(qdisc_dev(sch));
	WRITE_ONCE(sch->limit, limit);
    } else {
        struct tc_bfifo_cc_qopt *ctl = nla_data(opt);
        if (nla_len(opt) < sizeof(*ctl))
	    return -EINVAL;
        WRITE_ONCE(sch->limit, ctl->limit);
        if (ctl->queue_control >= 0) {
			WRITE_ONCE(q->queue_control, ctl->queue_control);
		} else {
			return -EINVAL;

       }
    }
    return 0;
}

static int bfifo_cc_dump(struct Qdisc *sch, struct sk_buff *skb) {

    struct bfifo_cc_sched_data *q = SCH_bfifo_cc(sch);

    struct tc_bfifo_cc_qopt opt = {
        .limit = READ_ONCE(sch->limit),
        .queue_control = READ_ONCE(q->queue_control),
    };

    return nla_put(skb, TCA_OPTIONS, sizeof(opt), &opt);
}


static void bfifo_cc_destroy(struct Qdisc *sch)
{
    struct bfifo_cc_sched_data *q = SCH_bfifo_cc(sch);
	struct ecn_skb_node *node, *tmp;

	spin_lock_bh(&q->lock);
	list_for_each_entry_safe(node, tmp, &q->ecn_list, list) {
		list_del(&node->list);
		kmem_cache_free(ecn_node_cache, node);
	}
	spin_unlock_bh(&q->lock);

	q->ecn_count = 0;
	qdisc_reset_queue(sch);
}

struct Qdisc_ops bfifo_cc_qdisc_ops __read_mostly ={
	.id		    =	"bfifo_cc",
	.priv_size	=	sizeof(struct bfifo_cc_sched_data),
	.enqueue	=	bfifo_cc_enqueue,
	.dequeue	=	bfifo_cc_dequeue,
	.peek		=	qdisc_peek_head,
	.init		=	bfifo_cc_init,
	.destroy	=	bfifo_cc_destroy,
	.reset		=	bfifo_cc_reset,
	.change		=	bfifo_cc_init,
	.dump		=	bfifo_cc_dump,
	.owner		=	THIS_MODULE,
};
MODULE_ALIAS("sch_bfifo_cc");

static int __init bfifo_cc_module_init(void)
{
	ecn_node_cache = kmem_cache_create("ecn_node_cache", sizeof(struct ecn_skb_node), 0, 0, NULL);

	if (!ecn_node_cache)
		return -ENOMEM;

	if (register_qdisc(&bfifo_cc_qdisc_ops)) {
		kmem_cache_destroy(ecn_node_cache);
		return -EINVAL;
	}
	trace_printk("ecn_node_cache created\n");
	return 0;
}

static void __exit bfifo_cc_module_exit(void)
{
	unregister_qdisc(&bfifo_cc_qdisc_ops);
	kmem_cache_destroy(ecn_node_cache);
}

module_init(bfifo_cc_module_init)
module_exit(bfifo_cc_module_exit)
MODULE_AUTHOR("Aitor Encinas Alonso");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("BFIFO with Color Packet Control qdisc");
EXPORT_SYMBOL(bfifo_cc_qdisc_ops);
