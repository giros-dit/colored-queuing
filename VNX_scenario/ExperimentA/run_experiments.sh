#!/bin/bash

lxc-attach -n marker -- bash ./root/ExperimentA/marker_conf1.sh


echo "==== EXPERIMENTO 1 ===="
lxc-attach -n router -- bash ./root/ExperimentA/PE1_conf_mode1.sh
./captura.sh exp1 &
CAP_PID=$!

wait $CAP_PID

echo "==== EXPERIMENTO 2 ===="
lxc-attach -n router -- bash ./root/ExperimentA/PE1_conf_threshold1.sh
./captura.sh exp2 &
CAP_PID=$!

wait $CAP_PID

lxc-attach -n marker -- bash ./root/ExperimentA/marker_conf2.sh

echo "==== EXPERIMENTO 3 ===="
lxc-attach -n router -- bash ./root/ExperimentA/PE1_conf_threshold2.sh
./captura.sh exp3 &
CAP_PID=$!

wait $CAP_PID

echo "==== TODOS LOS EXPERIMENTOS COMPLETADOS ===="

python3 comparation.py
