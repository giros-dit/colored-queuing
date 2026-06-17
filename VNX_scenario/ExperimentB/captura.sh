#!/bin/bash

EXP_NAME=$1

echo "Iniciando captura: $EXP_NAME"

mkdir -p capturas
chmod 777 capturas

FILE1="capturas/${EXP_NAME}_router-e1.pcap"
FILE2="capturas/${EXP_NAME}_router-e2.pcap"

wireshark -i router-e1 -k -f "udp && !icmp" -w $FILE1 &
PID1=$!

wireshark -i router-e2 -k -f "udp && !icmp" -w $FILE2 &
PID2=$!

sleep 15

tcpreplay --intf1=marker-e1 ExperimentB.pcap

sleep 10

read

kill -2 $PID1 $PID2
wait

echo "Capturas guardadas como:"
echo "$FILE1"
echo "$FILE2"
