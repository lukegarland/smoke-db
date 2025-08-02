#!/bin/bash

source venv/bin/activate

cd docker
docker-compose up -d
cd ../python
python probe_reader.py
