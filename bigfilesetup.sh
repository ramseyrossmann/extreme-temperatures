cd pickles/
tar -xvzf gams-data-midwest.tar.gz
rm gams-data-midwest.tar.gz
cd ..

python combinearrays.py

rm -r bigdatafilesplit/
