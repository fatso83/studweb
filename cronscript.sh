#!/bin/sh
# To run using cron, simply type `crontab cron_example`
PYTHONPATH=~carlerik/lib/python-2.7/site-packages
PYTHON=~carlerik/bin/python2.7
SCRIPT=$(dirname $0)/studweb.py

# Run script
$PYTHON $SCRIPT --quiet
