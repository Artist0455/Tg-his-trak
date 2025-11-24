#!/bin/bash
python app.py &
gunicorn app:web_app --bind 0.0.0.0:$PORT
