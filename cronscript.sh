#!/bin/sh
PYTHONPATH=~carlerik/lib/python-2.7/site-packages
PYTHON=~carlerik/bin/python2.7
SCRIPT=$(dirname $0)/studweb.py

# Run script
$PYTHON $SCRIPT $@
