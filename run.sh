#!/bin/bash

# Run Django migrations
python manage.py migrate

# Start Django server
python manage.py runserver 0.0.0.0:8000 &

# Start the Pub/Sub subscriber
python manage.py subscriber