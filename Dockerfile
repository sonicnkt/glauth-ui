FROM python:3.10-alpine AS builder

ARG PUID=1000
RUN adduser -D -u ${PUID} ldap
WORKDIR /home/ldap

RUN apk add --no-cache postgresql-libs && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev
COPY requirements.txt .
RUN python -m venv venv && \
    venv/bin/pip install --no-cache-dir gunicorn && \
    venv/bin/pip install --no-cache-dir -r requirements.txt && \
    apk --purge del .build-deps

FROM python:3.10-alpine

RUN apk add --no-cache postgresql-libs

ARG PUID=1000
RUN adduser -D -u ${PUID} ldap

WORKDIR /home/ldap
COPY --from=builder /home/ldap/venv ./venv
COPY . .

RUN set -x \
 && mkdir -p db logs \
 && chown -R ldap:ldap db logs

ENV FLASK_APP ldap.py

USER ldap

VOLUME ["/home/ldap/db"]

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]