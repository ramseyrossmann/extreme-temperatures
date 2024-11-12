#!/bin/bash
filename=${1}'results-data.txt'
while IFS=, read -r extreme U tag
do
  mv results_${extreme}_U${U}_${tag}.pkl ${1}results/${extreme}/U${U}_${tag}.pkl
done < $filename
