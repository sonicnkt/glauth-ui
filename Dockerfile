FROM alpine:3.13

#Authlib depends on py3-cryptography but there aren't 
# any muscl-libc (alpine) compatible python wheels.
RUN apk add --no-cache python3 py3-cryptography py3-pip py3-virtualenv

RUN adduser -D ldap

WORKDIR /home/ldap

COPY requirements.txt requirements.txt
RUN python3 -m venv --system-site-packages venv
RUN venv/bin/pip install --no-cache-dir -r requirements.txt
RUN venv/bin/pip install --no-cache-dir gunicorn

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
