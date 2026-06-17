from scapy.all import rdpcap, IP, UDP
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import subprocess
import re
import struct


experiments = ["exp1", "exp2", "exp3", "exp4", "exp5"]

my_flows = ["10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"]

step = 0.01
step_lat = 0.005
step_loss = 0.001

def process_experiment(exp_name):
    pkts_sent = rdpcap(f"capturas/{exp_name}_router-e1.pcap")
    pkts_received = rdpcap(f"capturas/{exp_name}_router-e2.pcap")

    src_ips = set()
    sent_dict = {}
    bw_sent_by_flow = defaultdict(lambda: defaultdict(float))
    t0 = min(pkt.time for pkt in pkts_sent if IP in pkt)

    for pkt in pkts_sent:
        if IP in pkt and UDP in pkt:
            interval = int((pkt.time -t0) / step + 1)

            bw_sent_by_flow[pkt[IP].src][interval] += len(pkt) * 8
            src_ips.add(pkt[IP].src)
            seq = struct.unpack("!I", bytes(pkt[UDP].payload)[:4])[0]
            key = (pkt[IP].src, pkt[IP].dst, seq)
            sent_dict[key] = { "time": pkt.time, "dscp": pkt[IP].tos >> 2 }

    delay_by_flow = defaultdict(list) # List of (recv_time, delay)
    bw_by_flow = defaultdict(lambda: defaultdict(float)) # src_ip -> intervalo -> bps

    for pkt in pkts_received:
        if IP in pkt and UDP in pkt:
            seq = struct.unpack("!I", bytes(pkt[UDP].payload)[:4])[0]
            key = (pkt[IP].src, pkt[IP].dst, seq)
            recv_time = pkt.time
            if key in sent_dict:
                delay = recv_time - sent_dict[key]["time"]
                delay_by_flow[pkt[IP].src].append((recv_time, delay))
                interval = int((recv_time - t0)/step_lat + 1)
                bw_by_flow[pkt[IP].src][interval] += len(pkt) * 8
                del sent_dict[key]  # Marked as received

    
    lost_by_flow_green = defaultdict(int)
    lost_by_flow_yellow = defaultdict(int)

    # Lo que queda en sent_dict son paquetes no recibidos
    for (src_ip, pkt_id, seq), info in sent_dict.items():
        dscp = info["dscp"]
        for ip in my_flows:
            if src_ip == ip:
                if dscp == 0:
                    lost_by_flow_green[ip] += 1
                else:
                    lost_by_flow_yellow[ip] += 1
                break


    grouped_delays = defaultdict(lambda: defaultdict(list)) # src_ip -> interval -> list of delays
    for src_ip, values in delay_by_flow.items():
        for recv_time, delay in values:
            interval = int((recv_time - t0) / step_lat + 1)
            grouped_delays[src_ip][interval].append(delay)

    all_intervals = set()
    for intervals in grouped_delays.values():
        all_intervals.update(intervals.keys())


    max_interval = max(all_intervals)

    for ip, intervals in grouped_delays.items():
        for interval in range(max_interval + 1):
            if interval not in intervals:
                grouped_delays[ip][interval] = [0]

    for ip, intervals in bw_sent_by_flow.items():
        for interval in range(max_interval + 1):
            if interval not in intervals:
                bw_sent_by_flow[ip][interval] = [0]

    for ip, intervals in bw_by_flow.items():
        for interval in range(max_interval + 1):
            if interval not in intervals:
                bw_by_flow[ip][interval] = [0]

    for ip in my_flows:
        if not lost_by_flow_green[ip]:
            lost_by_flow_green[ip] = 0
        if not lost_by_flow_yellow[ip]:
            lost_by_flow_yellow[ip]= 0

    return bw_sent_by_flow, bw_by_flow, grouped_delays, lost_by_flow_green, lost_by_flow_yellow


exp_styles = {
    "exp1": dict(linestyle='-', label='DAPO'),
    "exp2": dict(linestyle='--', label='Threshold c1'),
    "exp3": dict(linestyle='--', label='Threshold c2'),
    "exp4": dict(linestyle=':', label='bfifo'),
    "exp5": dict(linestyle='-', label='RED')
}

size=2
line_size=1
# ---------------------------------
# Style configuration per flow
# ---------------------------------

flow_styles = {
    "10.0.0.2":  dict(label='flow1', color='#CC0000', marker='*', linestyle='-', markersize=size, linewidth=line_size),
    "10.0.0.3":  dict(label='flow2', color='#FF9999', marker='^', linestyle='-', markersize=size, linewidth=line_size),
    "10.0.0.4":  dict(label='flow4', color='#3333FF', marker='o', linestyle='-', markersize=size, linewidth=line_size),
    "10.0.0.5":  dict(label='flow3', color='#007FFF', marker='^', linestyle='-', markersize=size, linewidth=line_size)
}

# Plot Generated Traffic
plt.figure(figsize=(10,7))

bw_sent_by_flow, _, _, _, _ = process_experiment("exp1")
exp_style = exp_styles.get("exp1")

for ip, intervals in bw_sent_by_flow.items():
    style = flow_styles.get(ip)
    x = sorted(intervals)
    y = [bw_sent_by_flow[ip][i] / step / 1e6 for i in x]  # Mbps
    vector1 = [i*step*1000 for i in x]  # ms
    
    if style:
        plt.plot(vector1, y, label=style["label"], color=style["color"], marker=style["marker"], linestyle=exp_style["linestyle"], markersize=style["markersize"], linewidth=style["linewidth"])
plt.xlabel("t (ms)")
plt.ylabel("BW (Mbps)")
plt.grid(True)
#plt.ylim(0,80)
plt.xlim(0,1000)
plt.tight_layout()

# Plot bandwidth

for exp in experiments:

    plt.figure(figsize=(10,7))
    _, bw_by_pair, _ = process_experiment(exp)
    exp_style = exp_styles.get(exp)
    for (ip1, ip2), intervals in bw_by_pair.items():
        style = flow_styles.get(ip1)
        x = sorted(intervals)
        y = [intervals[i] / step_lat / 1000000 for i in x]  # bits por 10ms => bits/s
        vector1 = [i*step_lat*1000 for i in x]

        if style:
            plt.plot(vector1, y, label=style["label"], color=style["color"], marker=style["marker"], linestyle=exp_style["linestyle"], markersize=style["markersize"], linewidth=style["linewidth"])

    plt.xlabel("t (ms)")
    plt.ylabel("BW (Mbps)")
    plt.grid(True)
    plt.ylim(0,70)
    #plt.xlim(0,1000)
    #plt.legend()
    plt.tight_layout()

# Plot the delays
for exp in experiments:

    plt.figure(figsize=(10,7))
    _, _, delay_by_pair = process_experiment(exp)
    exp_style = exp_styles.get(exp)

    for (ip1, ip2), intervals in delay_by_pair.items():
        style = flow_styles.get(ip1)
        x = []
        y = []
        for interval in sorted(intervals):
            max_delay = max(intervals[interval])
            x.append(interval * step_lat * 1000)
            y.append(max_delay * 1000)

        if style:
            plt.plot(x, y, label=style["label"], color=style["color"], marker=style["marker"], linestyle=exp_style["linestyle"], markersize=style["markersize"], linewidth=style["linewidth"])

plt.xlabel("t (ms)")
plt.ylabel("Latency (ms)")
plt.grid(True)
#plt.legend()
plt.ylim(0,30)
#plt.xlim(0,1000)
plt.tight_layout()


# Plot packet losses
plt.figure(figsize=(10,7))

bar_width = 0.2

pairs = [flow_styles[ip1]["label"] for ip1, ip2 in my_flows]
exps = [exp_styles[exp]["label"] for exp in experiments]

x = np.arange(len(pairs))

for idx, exp in enumerate(experiments):

    lost_green, lost_yellow = process_losses(exp)

    values_green = []
    values_yellow = []
    xpos = []

    for i, (ip1, ip2) in enumerate(my_flows):

        v0 = lost_green.get((ip1, ip2), 0)
        v1 = lost_yellow.get((ip1, ip2), 0)

        values_green.append(v0)
        values_yellow.append(v1)

        offset = (i - (len(pairs)-1)/2) * bar_width
        xpos.append(idx + offset)

    plt.bar(
        xpos,
        values_green,
        width=bar_width,
        color='green'
    )

    plt.bar(
        xpos,
        values_yellow,
        width=bar_width,
        bottom=values_green,
        color='yellow'
    )

    print(f"Experiment: {exp}")
    print(pairs)
    print(xpos)

    for i in range(len(xpos)):

        total = values_green[i] + values_yellow[i]

        plt.text(
            xpos[i],
            total + 0.2,
            pairs[i],
            ha='center',
            fontsize=8,
            rotation=90
        )
#plt.xticks(x,pairs)
plt.xticks(np.arange(len(experiments)), exps)     
plt.xlabel("Queue Buffer Scheme")
plt.ylabel("Dropped Packets")
plt.grid(False)
plt.tight_layout()

plt.show()
