#!/bin/bash

virtualenv venv # -p python3.11 ## for a specific Python version
source venv/bin/activate
pip install -r python/requirements.txt
