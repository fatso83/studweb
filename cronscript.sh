#!/bin/sh
# To run using cron, run `crontab -e` and input the following line 
# * * * * * ~carlerik/src/studweb/studweb.py
PYTHONPATH=~carlerik/lib/python-2.7/site-packages
PYTHON=~carlerik/bin/python2.7
SCRIPT=$(dirname $0)/studweb.py

# Run script
$PYTHON $SCRIPT 
