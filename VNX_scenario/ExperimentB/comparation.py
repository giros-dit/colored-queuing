from scapy.all import rdpcap, IP, UDP
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import subprocess
import re
import struct

def tikz_save(filename):
    import tikzplotlib
    tikzplotlib.save(filename, axis_width='\\textwidth', axis_height='0.7\\textwidth')


experiments = ["exp1", "exp2", "exp3", "exp4", "exp5"]

my_flows = ["10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"]

step = 0.01
step_lat = 0.01

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
                #bw_by_flow[pkt[IP].src][interval] += len(pkt) * 8
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
                bw_sent_by_flow[ip][interval] = 0

    # for ip, intervals in bw_by_flow.items():
    #     for interval in range(max_interval + 1):
    #         if interval not in intervals:
    #             bw_by_flow[ip][interval] = 0

    for ip in my_flows:
        if not lost_by_flow_green[ip]:
            lost_by_flow_green[ip] = 0
        if not lost_by_flow_yellow[ip]:
            lost_by_flow_yellow[ip]= 0

    return bw_sent_by_flow, grouped_delays, lost_by_flow_green, lost_by_flow_yellow


exp_styles = {
    "exp1": dict(linestyle='-', label='DAPO'),
    "exp2": dict(linestyle='-', label='Th.(c.i)'),
    "exp3": dict(linestyle='-', label='Th.(c.ii)'),
    "exp4": dict(linestyle='-', label='FIFO'),
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
    "10.0.0.4":  dict(label='flow3', color='#3333FF', marker='o', linestyle='-', markersize=size, linewidth=line_size),
    "10.0.0.5":  dict(label='flow4', color='#007FFF', marker='^', linestyle='-', markersize=size, linewidth=line_size)
}

results = {}

for exp in experiments:
    bw_sent_by_flow, grouped_delays, lost_by_flow_green, lost_by_flow_yellow = process_experiment(exp)

    results[exp] = {
        "bw_sent_by_flow": bw_sent_by_flow,
        "grouped_delays": grouped_delays,
        "lost_by_flow_green": lost_by_flow_green,
        "lost_by_flow_yellow": lost_by_flow_yellow
    }


# # Plot Generated Traffic
# plt.figure(figsize=(10,7))

# bw_sent = results["exp1"]["bw_sent_by_flow"]
# exp_style = exp_styles.get("exp1")

# for ip, intervals in bw_sent.items():
#     style = flow_styles.get(ip)
#     x = sorted(intervals)
#     y = [bw_sent[ip][i] / step / 1e6 for i in x]  # Mbps
#     vector1 = [i*step*1000 for i in x]  # ms
    
#     if style:
#         plt.plot(vector1, y, label=style["label"], color=style["color"], marker=style["marker"], linestyle=exp_style["linestyle"], markersize=style["markersize"], linewidth=style["linewidth"])
# plt.xlabel("t (ms)")
# plt.ylabel("BW (Mbps)")
# plt.grid(True)
# plt.ylim(0,80)
# plt.xlim(0,1000)
# plt.tight_layout()

# # Plot bandwidth
# for exp in experiments:

#     plt.figure(figsize=(10,7))
#     bw = results[exp]["bw_by_flow"]
#     exp_style = exp_styles.get(exp)

#     for ip, intervals in bw.items():
#         style = flow_styles.get(ip)
#         x = []
#         y = []
#         x = sorted(intervals)
#         y = [intervals[i] / step / 1000000 for i in x]  # bits por 10ms => bits/s
#         vector1 = [i*step_lat*1000 for i in x]

#         if style:
#             plt.plot(vector1, y, label=style["label"], color=style["color"], marker=style["marker"], linestyle=exp_style["linestyle"], markersize=style["markersize"], linewidth=style["linewidth"])

#     plt.xlabel("t (ms)")
#     plt.ylabel("BW (Mbps)")
#     plt.grid(True)
#     plt.ylim(0,70)
#     #plt.xlim(0,1000)
#     #plt.legend()
#     plt.tight_layout()

# Plot the delays
for exp in experiments:

    plt.figure(figsize=(10,7))
    lat = results[exp]["grouped_delays"]
    exp_style = exp_styles.get(exp)

    for ip, intervals in lat.items():
        style = flow_styles.get(ip)
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
    plt.xlim(0,5000)
    plt.tight_layout()
    tikz_save(f"lat_expb_{exp}.tex")

# Plot Maximum delays
plt.figure(figsize=(10,7))

bar_width = 0.2

pairs = [flow_styles[ip]["label"] for ip in my_flows]
exps = [exp_styles[exp]["label"] for exp in experiments]

x = np.arange(len(my_flows))

for idx, exp in enumerate(experiments):

    lat = results[exp]["grouped_delays"] 
    
    lat_values = []
    xpos = []
    colors = []

    for i, ip in enumerate(my_flows):

        offset = (i - (len(my_flows)-1)/2) * bar_width
        xpos.append(idx + offset)

        if ip in lat:
            lat_values.append(max(np.max(v) for v in lat[ip].values()))
            colors.append(flow_styles[ip]["color"])

    plt.bar(
        xpos,
        lat_values,
        width=bar_width,
        color=colors
    )

    print(f"Experiment: {exp}")
    print(pairs)
    print(xpos)

    for i in range(len(xpos)):

        total = lat_values[i]

        plt.text(
            xpos[i],
            total + 2,
            pairs[i],
            ha='center',
            fontsize=10,
            rotation=90
        )
#plt.xticks(x,pairs)
plt.xticks(np.arange(len(experiments)), exps)     
plt.xlabel("Queue Buffer Scheme")
plt.ylabel("Maximum Delay (ms)")
plt.grid(False)
plt.tight_layout()
tikz_save(f"lat_max_expb.tex")

    
plt.figure(figsize=(10,7))

bar_width = 0.2

pairs = [flow_styles[ip]["label"] for ip in my_flows]
exps = [exp_styles[exp]["label"] for exp in experiments]

x = np.arange(len(my_flows))

for idx, exp in enumerate(experiments):

    lost_green = results[exp]["lost_by_flow_green"]
    lost_yellow = results[exp]["lost_by_flow_yellow"]   
    
    values_green = []
    values_yellow = []
    xpos = []

    for i, ip in enumerate(my_flows):

        offset = (i - (len(my_flows)-1)/2) * bar_width
        xpos.append(idx + offset)

        values_green.append(lost_green[ip])
        values_yellow.append(lost_yellow[ip])

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
            total+20,
            pairs[i],
            ha='center',
            fontsize=11,
            rotation=90
        )
#plt.xticks(x,pairs)
plt.xticks(np.arange(len(experiments)), exps)     
plt.xlabel("Queue Buffer Scheme")
plt.ylabel("Dropped Packets")
plt.grid(False)
plt.tight_layout()
tikz_save(f"lost_expb.tex")

plt.show()
