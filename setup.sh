#!/bin/bash

virtualenv venv -p python3.11
source venv/bin/activate
pip install -r python/requirements.txt