from scapy.all import rdpcap, IP, UDP
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import struct

def tikz_save(filename):
    import tikzplotlib
    tikzplotlib.save(filename, axis_width='\\textwidth', axis_height='0.7\\textwidth')


experiments = ["exp1", "exp2", "exp3"]

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
    max_interval_losses = 0

    for pkt in pkts_sent:
        if IP in pkt and UDP in pkt:
            interval = int((pkt.time -t0) / step)
            if interval > max_interval_losses:
                max_interval_losses = interval

            bw_sent_by_flow[pkt[IP].src][interval] += len(pkt) * 8
            src_ips.add(pkt[IP].src)
            seq = struct.unpack("!I", bytes(pkt[UDP].payload)[:4])[0]
            key = (pkt[IP].src, pkt[IP].dst, seq)
            sent_dict[key] = pkt.time

    delay_by_flow = defaultdict(list) # List of (recv_time, delay)
    bw_by_flow = defaultdict(lambda: defaultdict(float)) # src_ip -> intervalo -> bps

    for pkt in pkts_received:
        if IP in pkt and UDP in pkt:
            seq = struct.unpack("!I", bytes(pkt[UDP].payload)[:4])[0]
            key = (pkt[IP].src, pkt[IP].dst, seq)
            recv_time = pkt.time
            if key in sent_dict:
                delay = recv_time - sent_dict[key]
                delay_by_flow[pkt[IP].src].append((recv_time, delay))
                interval = int((recv_time - t0)/step)
                bw_by_flow[pkt[IP].src][interval] += len(pkt) * 8
                del sent_dict[key]  # Marked as received
    
    lost_by_flow_interval = defaultdict(lambda: defaultdict(int))

    # paquetes perdidos (los que quedan en sent_dict)
    for (src_ip, dst_ip, seq), send_time in sent_dict.items():
        interval = int((send_time - t0) / step)
        lost_by_flow_interval[src_ip][interval] += 1     

    grouped_delays = defaultdict(lambda: defaultdict(list)) # src_ip -> interval -> list of delays
    for src_ip, values in delay_by_flow.items():
        for recv_time, delay in values:
            interval = int((recv_time - t0) / step_lat)
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

    for ip, intervals in bw_by_flow.items():
        for interval in range(max_interval + 1):
            if interval not in intervals:
                bw_by_flow[ip][interval] = 0

    for ip, intervals in lost_by_flow_interval.items():
        for interval in range(max_interval_losses + 1):
            if interval not in intervals:
                lost_by_flow_interval[ip][interval] = 0 

    return bw_sent_by_flow, bw_by_flow, grouped_delays, lost_by_flow_interval


exp_styles = {
    "exp1": dict(linestyle='-', label='DAPO'),
    "exp2": dict(linestyle='-', label='Threshold c1'),
    "exp3": dict(linestyle='-', label='Threshold c2')
}

size=1
line_size=1
# ---------------------------------
# Style configuration per flow
# ---------------------------------

flow_styles = {
    "10.0.0.2":  dict(label='flow1', color='#CC0000', marker='*', linestyle='-', markersize=1.5*size, linewidth=2*line_size, zorder=3),
    "10.0.0.3":  dict(label='flow2', color='#FF9999', marker='^', linestyle='-', markersize=size, linewidth=line_size, zorder=4),
    "10.0.0.4":  dict(label='flow3', color='#3333FF', marker='o', linestyle='-', markersize=1.5*size, linewidth=2*line_size, zorder=1),
    "10.0.0.5":  dict(label='flow4', color="#7DE1FFFF", marker='^', linestyle='-', markersize=size, linewidth=line_size, zorder=2)
}

results = {}

for exp in experiments:
    bw_sent_by_flow, bw_by_flow, grouped_delays, lost_by_flow_interval = process_experiment(exp)

    results[exp] = {
        "bw_sent_by_flow": bw_sent_by_flow,
        "bw_by_flow": bw_by_flow,
        "grouped_delays": grouped_delays,
        "lost_by_flow_interval": lost_by_flow_interval,
    }


# Plot Generated Traffic
plt.figure(figsize=(10,7))

bw_sent = results["exp1"]["bw_sent_by_flow"]
exp_style = exp_styles.get("exp1")

for ip, intervals in bw_sent.items():
    style = flow_styles.get(ip)
    x = sorted(intervals)
    y = [bw_sent[ip][i] / step / 1e6 for i in x]  # Mbps
    vector1 = [i*step*1000 for i in x]  # ms
    
    if style:
        plt.plot(vector1, y, label=style["label"], color=style["color"], marker=style["marker"], linestyle=exp_style["linestyle"], markersize=style["markersize"], linewidth=style["linewidth"], zorder=style["zorder"])
plt.xlabel("t (ms)")
plt.ylabel("BW (Mbps)")
plt.grid(True)
#plt.ylim(0,80)
#plt.xlim(0,1000)
plt.tight_layout()

# fig = plt.gcf()
# handles, labels = plt.gca().get_legend_handles_labels()
# fig_legend = plt.figure(figsize=(4, 2))
# fig_legend.legend(
#     handles,
#     labels,
#     loc='center',
#     ncol=4,   # <- clave
#     frameon=False
# )
# fig_legend.savefig("legend.pdf", bbox_inches='tight')
# plt.close(fig_legend)

tikz_save("bw_gen_expa.tex")

# Plot bandwidth
for exp in experiments:

    plt.figure(figsize=(10,7))
    bw = results[exp]["bw_by_flow"]
    exp_style = exp_styles.get(exp)

    for ip, intervals in bw.items():
        style = flow_styles.get(ip)
        x = []
        y = []
        x = sorted(intervals)
        y = [intervals[i] / step / 1000000 for i in x]  # bits por 10ms => bits/s
        vector1 = [i*step*1000 for i in x]

        if style:
            plt.plot(vector1, y, label=style["label"], color=style["color"], marker=style["marker"], linestyle=exp_style["linestyle"], markersize=style["markersize"], linewidth=style["linewidth"], zorder=style["zorder"])

    plt.xlabel("t (ms)")
    plt.ylabel("BW (Mbps)")
    plt.grid(True)
    plt.ylim(0,70)
    plt.xlim(0,5000)
    #plt.legend()
    plt.tight_layout()
    tikz_save(f"bw_expa_{exp}.tex")

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
            plt.plot(x, y, label=style["label"], color=style["color"], marker=style["marker"], linestyle=exp_style["linestyle"], markersize=style["markersize"], linewidth=style["linewidth"], zorder=style["zorder"])

    plt.xlabel("t (ms)")
    plt.ylabel("Latency (ms)")
    plt.grid(True)
    #plt.legend()
    plt.ylim(0,30)
    plt.xlim(0,5000)
    plt.tight_layout()
    tikz_save(f"lat_expa_{exp}.tex")

for exp in experiments:
    
    plt.figure(figsize=(10,7))
    losses = results[exp]["lost_by_flow_interval"]
    exp_style = exp_styles.get(exp)

    for ip, intervals in losses.items():
        style = flow_styles.get(ip)
        x = []
        y = []
        x = sorted(intervals)
        y = [intervals[i] for i in x]
        vector1 = [i * step * 1000 for i in x]  # ms

        if style:
            plt.plot(vector1, y,
                    label=style["label"],
                    color=style["color"],
                    marker=style["marker"],
                    linestyle=exp_style["linestyle"],
                    markersize=style["markersize"],
                    linewidth=style["linewidth"])

    plt.xlabel("t (ms)")
    plt.ylabel("Lost Packets")
    plt.grid(True)
    plt.xlim(0,5000)
    plt.tight_layout()
    tikz_save(f"loss_expa_{exp}.tex")
plt.show()
