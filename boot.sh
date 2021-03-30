#!/bin/sh
source venv/bin/activate
flask db upgrade
flask createdbdata
exec gunicorn -b :5000 --access-logfile - --error-logfile - ldap:app