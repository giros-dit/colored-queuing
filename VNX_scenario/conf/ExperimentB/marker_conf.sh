sudo brctl addbr br0
sudo ip link set br0 up
sudo brctl addif br0 eth1
sudo brctl addif br0 eth2
sudo ip link set eth1 up
sudo ip link set eth2 up


echo "Deleting previous qdisc"
tc qdisc del dev eth1 ingress

echo "Creating ingress qdisc"
tc qdisc add dev eth1 ingress handle ffff:

echo "Installing filters"
tc filter add dev eth1 protocol ip parent ffff: prio 1 u32 \
    match ip src 10.0.0.2 \
    police rate 30mbit burst 37050b continue 

tc filter add dev eth1 protocol ip parent ffff: prio 2 u32 \
    match ip src 10.0.0.2 \
    action pedit ex munge ip dsfield set 0x10 retain 0xfe \
    pipe \
    action csum ip and udp

tc filter add dev eth1 protocol ip parent ffff: prio 1 u32 \
    match ip src 10.0.0.3 \
    police rate 30mbit burst 37050b continue 

tc filter add dev eth1 protocol ip parent ffff: prio 2 u32 \
    match ip src 10.0.0.3 \
    action pedit ex munge ip dsfield set 0x10 retain 0xfe \
    pipe \
    action csum ip and udp

tc filter add dev eth1 protocol ip parent ffff: prio 1 u32 \
    match ip src 10.0.0.4 \
    police rate 20mbit burst 74500b continue 

tc filter add dev eth1 protocol ip parent ffff: prio 2 u32 \
    match ip src 10.0.0.4 \
    action pedit ex munge ip dsfield set 0x10 retain 0xfe \
    pipe \
    action csum ip and udp

tc filter add dev eth1 protocol ip parent ffff: prio 1 u32 \
    match ip src 10.0.0.5 \
    police rate 20mbit burst 74500b continue 

tc filter add dev eth1 protocol ip parent ffff: prio 2 u32 \
    match ip src 10.0.0.5 \
    action pedit ex munge ip dsfield set 0x10 retain 0xfe \
    pipe \
    action csum ip and udp

