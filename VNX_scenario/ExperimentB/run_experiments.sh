#!/bin/bash

lxc-attach -n marker -- bash ./root/ExperimentB/marker_conf.sh


echo "==== EXPERIMENTO 1 ===="
lxc-attach -n router -- bash ./root/ExperimentB/PE1_conf_mode1.sh
./captura.sh exp1 &
CAP_PID=$!

wait $CAP_PID

echo "==== EXPERIMENTO 2 ===="
lxc-attach -n router -- bash ./root/ExperimentB/PE1_conf_threshold1.sh
./captura.sh exp2 &
CAP_PID=$!

wait $CAP_PID

echo "==== EXPERIMENTO 3 ===="
lxc-attach -n router -- bash ./root/ExperimentB/PE1_conf_threshold2.sh
./captura.sh exp3 &
CAP_PID=$!

wait $CAP_PID

echo "==== EXPERIMENTO 4 ===="
lxc-attach -n router -- bash ./root/ExperimentB/PE1_conf.sh
./captura.sh exp4 &
CAP_PID=$!

wait $CAP_PID

echo "==== EXPERIMENTO 5 ===="
lxc-attach -n router -- bash ./root/ExperimentB/PE1_conf_red.sh
./captura.sh exp5 &
CAP_PID=$!

wait $CAP_PID

echo "==== TODOS LOS EXPERIMENTOS COMPLETADOS ===="

python3 comparation.py
