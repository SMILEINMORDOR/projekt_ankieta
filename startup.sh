#!/bin/bash
apt-get update && apt-get install -y unixodbc-dev g++
pip install --upgrade pip
pip install -r requirements.txt

gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app
