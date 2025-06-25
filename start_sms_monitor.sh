#!/bin/bash
# Script de démarrage pour le monitoring SMS

cd /path/to/BestConnect
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=backend.settings
python sms_handler.py