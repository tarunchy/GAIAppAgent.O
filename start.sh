#!/bin/bash
source ~/jupyterlab/jupyterlab_env/bin/activate
nohup python app.py > output.log 2>&1 &
echo $! > pid.file