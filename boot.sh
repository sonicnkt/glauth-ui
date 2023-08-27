#!/bin/sh
source venv/bin/activate
flask db upgrade
flask createdbdata
exec gunicorn -b ${LISTEN_IP:-0.0.0.0}:${LISTEN_PORT:-5000} --access-logfile - --error-logfile - ldap:app
