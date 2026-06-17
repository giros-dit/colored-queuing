#include <linux/module.h>
#define INCLUDE_VERMAGIC
#include <linux/build-salt.h>
#include <linux/elfnote-lto.h>
#include <linux/export-internal.h>
#include <linux/vermagic.h>
#include <linux/compiler.h>

#ifdef CONFIG_UNWINDER_ORC
#include <asm/orc_header.h>
ORC_HEADER;
#endif

BUILD_SALT;
BUILD_LTO_INFO;

MODULE_INFO(vermagic, VERMAGIC_STRING);
MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};

#ifdef CONFIG_MITIGATION_RETPOLINE
MODULE_INFO(retpoline, "Y");
#endif



static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0x2b4cee43, "gnet_stats_copy_app" },
	{ 0xb19a5453, "__per_cpu_offset" },
	{ 0x9e683f75, "__cpu_possible_mask" },
	{ 0x53a1e8d9, "_find_next_bit" },
	{ 0x87a21cb3, "__ubsan_handle_out_of_bounds" },
	{ 0xe7e4dc6d, "tcf_block_put" },
	{ 0xded39a6b, "gen_kill_estimator" },
	{ 0xe7492fb4, "qdisc_put" },
	{ 0x37a0cba, "kfree" },
	{ 0xf53d4c26, "qdisc_class_hash_destroy" },
	{ 0xc3690fc, "_raw_spin_lock_bh" },
	{ 0xfc421e79, "gnet_stats_add_queue" },
	{ 0x1283e5b5, "qdisc_tree_reduce_backlog" },
	{ 0x85670f1d, "rtnl_is_locked" },
	{ 0xe46021ca, "_raw_spin_unlock_bh" },
	{ 0x1badaea8, "bfifo_cc_qdisc_ops" },
	{ 0xe7901fda, "pfifo_qdisc_ops" },
	{ 0x25b9fbe9, "qdisc_create_dflt" },
	{ 0xf03728c9, "noop_qdisc" },
	{ 0x54b1fac6, "__ubsan_handle_load_invalid_value" },
	{ 0x4c0de954, "qdisc_class_hash_remove" },
	{ 0x83f51840, "__nla_parse" },
	{ 0xf630261, "gen_replace_estimator" },
	{ 0x4c03a563, "random_kmalloc_seed" },
	{ 0xf116693b, "kmalloc_caches" },
	{ 0xd0e4bdda, "kmalloc_trace" },
	{ 0x866a62b2, "gnet_stats_basic_sync_init" },
	{ 0xc363e8c5, "qdisc_hash_add" },
	{ 0x7b9d9306, "qdisc_class_hash_insert" },
	{ 0x1ebe52f3, "qdisc_class_hash_grow" },
	{ 0xec2ebecf, "tcf_classify" },
	{ 0x5b8239ca, "__x86_return_thunk" },
	{ 0x65487097, "__x86_indirect_thunk_rax" },
	{ 0xbdfb6dbb, "__fentry__" },
	{ 0x790f5c3d, "register_qdisc" },
	{ 0xa84a0d8b, "qdisc_reset" },
	{ 0x56470118, "__warn_printk" },
	{ 0xa755349f, "unregister_qdisc" },
	{ 0xd9e19f3b, "tcf_block_get" },
	{ 0x117093be, "qdisc_class_hash_init" },
	{ 0xe6d2458e, "do_trace_netlink_extack" },
	{ 0x122c3a7e, "_printk" },
	{ 0x445c10bd, "nla_put" },
	{ 0x9bc9b231, "skb_trim" },
	{ 0xf0fdf6cb, "__stack_chk_fail" },
	{ 0x17de3d5, "nr_cpu_ids" },
	{ 0xc3793666, "gnet_stats_copy_basic" },
	{ 0x4a589753, "gnet_stats_copy_rate_est" },
	{ 0x4b777178, "gnet_stats_copy_queue" },
	{ 0x907364e, "module_layout" },
};

MODULE_INFO(depends, "sch_bfifo_cc");


MODULE_INFO(srcversion, "B3590ABDB28DA0D057E3C4F");
