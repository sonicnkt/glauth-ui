FROM python:3.10-alpine

RUN adduser -D ldap

WORKDIR /home/ldap

RUN apk add --no-cache postgresql-libs && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev
COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn
RUN apk --purge del .build-deps

COPY app app
COPY migrations migrations
COPY ldap.py config.py boot.sh ./
RUN set -x \
 && chmod +x boot.sh \
 && mkdir -p /home/ldap/db \
 && chown -R ldap:ldap ./

ENV FLASK_APP ldap.py

USER ldap

VOLUME ["/home/ldap/db"]

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]