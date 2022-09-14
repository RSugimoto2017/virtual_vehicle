#!/bin/bash

method=("suggestion")
schedule=("3" "8")
change_num=("10")
threshold=("3" "5" "10")

for m in ${method[@]}; do
  for s in ${schedule[@]}; do
    for n in ${change_num[@]}; do
      for t in ${threshold[@]}; do
        echo "simulation start...";
        echo "method:" $m;
        echo "schedule:" $s"am";
        echo "pseud_change_num": $n;
        echo "threshold:" $t;
        python $m.py $s $n $t --nogui
        sleep 3
      done;
    done;
  done;
done;