echo "Deleting previous qdisc"
tc qdisc del dev eth2 root

echo "Creating DRR"
# Set Link Speed
tc qdisc add dev eth2 root handle 1: htb 
tc class add dev eth2 parent 1: classid 1:1 htb rate 100mbit
tc qdisc add dev eth2 parent 1:1 handle 10: drr
tc class add dev eth2 parent 10: classid 10:1 drr quantum 2250
tc class add dev eth2 parent 10: classid 10:2 drr quantum 1500

tc qdisc add dev eth2 parent 10:1 handle 101: bfifo limit 125000
tc qdisc add dev eth2 parent 10:2 handle 102: bfifo limit 200000


echo "Installing filters"
tc filter add dev eth2 protocol ip parent 1:0 prio 0 u32 match ip src 10.0.0.0/24 classid 1:1
tc filter add dev eth2 protocol ip parent 10: prio 1 u32 match ip src 10.0.0.2 classid 10:1
tc filter add dev eth2 protocol ip parent 10: prio 1 u32 match ip src 10.0.0.3 classid 10:1
tc filter add dev eth2 protocol ip parent 10: prio 1 u32 match ip src 10.0.0.4 classid 10:2
tc filter add dev eth2 protocol ip parent 10: prio 1 u32 match ip src 10.0.0.5 classid 10:2

tc filter add dev eth2 protocol arp parent 1:1 prio 6 u32 match u32 0 0 classid 10:2
