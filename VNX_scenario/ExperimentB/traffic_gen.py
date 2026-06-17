from scapy.all import *
import time
import struct
from collections import defaultdict


# Duración de la simulación
duration1 = 1
duration2 = 4
packet_len = 1458
t0 = time.time()
pcap_packets = []
flow_seq = defaultdict(int)

host_macs = {
    "10.0.0.2": "00:00:00:00:01:02",
    "10.0.0.3": "00:00:00:00:01:03",
    "10.0.0.4": "00:00:00:00:01:04",
    "10.0.0.5": "00:00:00:00:01:05",
}

dst_mac = subprocess.check_output(
    ["sudo", "lxc-attach", "-n", "router", "--", "cat", "/sys/class/net/eth1/address"],
    text=True
).strip()

#dst_mac="fe:c6:ad:7c:a9:a3"


# Tráfico en ráfagas (isochronous)
bursts = [
    {"src": "10.0.0.2", "dst": "10.2.0.2", "interval": 0.5, "count": 24},   # h2 -> server2
    {"src": "10.0.0.3", "dst": "10.2.0.3", "interval": 0.5, "count": 24}, # h12 -> server12
    {"src": "10.0.0.4", "dst": "10.2.0.4", "interval": 0.5, "count": 49},  # h6 -> server6
    {"src": "10.0.0.5", "dst": "10.2.0.5", "interval": 0.5, "count": 49},   # h8 -> server8
]

# Flujos constantes (aprox. en pps)
const_flows = [
    {"src": "10.0.0.2", "dst": "10.2.0.2", "pps": 2500},    # h1-server1 (30 Mbps)
    {"src": "10.0.0.3", "dst": "10.2.0.3", "pps": 2500},     # h3-server3 (30 Mbps)
    {"src": "10.0.0.4", "dst": "10.2.0.4", "pps": 1666.6},    # h5-server5 (20 Mbps)
    {"src": "10.0.0.5", "dst": "10.2.0.5", "pps": 1666.6},    # h7-server7 (20 Mbps)
]

const_flows2 = [
    {"src": "10.0.0.2", "dst": "10.2.0.2", "pps": 5000},    # h1-server1 (60 Mbps)
    {"src": "10.0.0.3", "dst": "10.2.0.3", "pps": 1666.6},    # h5-server5 (20 Mbps)
    {"src": "10.0.0.4", "dst": "10.2.0.4", "pps": 833.3},    # h7-server7 (10 Mbps)
    {"src": "10.0.0.5", "dst": "10.2.0.5", "pps": 833.3},  # h9-server9 (10 Mbps)
]




# Generador de tráfico constante
def generate_constant(flow, t0, duration, start):
    packets = []
    interval = 1.0 / flow["pps"]
    pkt_count = int(duration * flow["pps"])
    
    flow_id = (flow["src"], flow["dst"])

    for i in range(pkt_count):
        pkt_time = t0 + start + i * interval
        src_ip = flow["src"]
        src_mac = host_macs[src_ip]

        flow_seq[flow_id] += 1
        seq = flow_seq[flow_id]

        payload = struct.pack("!I", seq) + b"x" * (packet_len - 4)

        eth = Ether(src=src_mac, dst=dst_mac, type=0x0800)
        pkt = eth / IP(src=flow["src"], dst=flow["dst"], id=i)/UDP(sport=1234, dport=5001)/Raw(load=payload)
        pkt.time = pkt_time
        packets.append(pkt)
    return packets

# Generador de ráfagas
def generate_burst(flow, t0, start, duration):
    packets = []
    burst_count = flow["count"] 
    interval = flow["interval"]
    flow_id = (flow["src"], flow["dst"])

    t = 0
    while t < duration:

        for i in range(burst_count):
            src_ip = flow["src"]
            src_mac = host_macs[src_ip]
            pkt_time = t0 + start + t + i * 0.000004

            flow_seq[flow_id] += 1
            seq = flow_seq[flow_id]

            payload = struct.pack("!I", seq) + b"x" * (packet_len - 4)

            eth = Ether(src=src_mac, dst=dst_mac, type=0x0800)
            pkt = eth / IP(src=flow["src"], dst=flow["dst"], id=i)/UDP(sport=1234, dport=5001)/Raw(load=payload)
            pkt.time = pkt_time
            packets.append(pkt)

        t += interval
    return packets

# Generar paquetes
for flow in const_flows:
    pcap_packets += generate_constant(flow, t0, duration1, 0)

for flow in const_flows2:
    pcap_packets += generate_constant(flow, t0, duration2, duration1)

for flow in bursts:
    pcap_packets += generate_burst(flow, t0, duration1, duration2)

# Ordenar por tiempo
pcap_packets.sort(key=lambda p: p.time)

# Guardar el resultado
wrpcap("ExperimentB.pcap", pcap_packets)
print("✔ PCAP con ráfagas y tráfico constante generado 'ExperimentB.pcap'")