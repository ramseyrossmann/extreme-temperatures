#!/bin/bash
filename=${1}'train-data.txt'
while IFS=, read -r S U
do
  mv solutions_S${S}_U${U}.pkl ${1}results/S${S}/U${U}/solutions.pkl
  mv data_S${S}_U${U}.pkl ${1}results/S${S}/U${U}/data.pkl
done < $filename

mkdir ${1}gurobi_sols/
ls *.sol > ${1}sol_list.txt
while read line
do
  mv $line ${1}gurobi_sols/
done < ${1}sol_list.txt
rm sol_list.txt
