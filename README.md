## glauth-ui

**Glauth-UI** is a small flask web app i created to manage the minimal [glauth ldap server](https://github.com/glauth/glauth).
I created this as i wanted to use glauth for authentication in several service at home and at work, but since it is readonly there is no way for users to configure their own password for example.

Since i knew a bit of python and wanted to learn flask i thought i create a small webapp that acts as a management ui for glauth. 

This should be considered as a prove of concept and some glauth features arent implemented yet as i have no use for them (yet). There are probably a lot of bugs in this and if you are using it you should limit the usage to the local network only. 


Current features:
 - Stores Data (Glauth Settings, Users, Groups) in a SQL DB (Sqlite, MySQL, PostgreSQL are supported) 
 - Generates a glauth compatible config.cfg file on every change to the db
 - Small UI for Endusers to change their password, name and email or reset their password (if forgotten).
 - Admin UI for managing settings and creating users and groups
 - eMail support for forgotten passwords and new user creation

Missing features:
 - Not all glauth settings and user options can be configured, following featurs and Options are missing:
    - API
    - Backend: nameformat, groupformat, sshkeyattr
    - User: loginShell, homeDir, sshkeys, passappsha256, otpsecret, yubikey 


### Installation:

The best installation method atm is to build the docker image with the included Dockerfile. 

1. Clone Repository
```
git clone https://github.com/sonicnkt/glauth-ui.git glauth-ui
```
2. Run docker build
```
cd glauth-ui
docker build -t glauthui:latest . 

```
3. Create container

`docker-compose.yaml`
```
version: '3.8'
services:
  glauthui:
    image: glauthui:latest
    container_name: glauthui
    restart: unless-stopped
    ports:
      - 80:5000
    volumes:
      # Mount Folder that contains DB and config file outside the container
      - './docker-data:/home/ldap/db'
    environment:
      - SECRET_KEY=mysuperlongsecretkeythatnobodywillguess
      # MAIL CONFIG
      - MAIL_SERVER=mail.example.com
      - MAIL_PORT=587
      - MAIL_USE_TLS=1
      - MAIL_USERNAME=username
      - MAIL_PASSWORD=password
      - MAIL_ADMIN=admin@example.com
```
`docker-compose up #-d`

On first startup (or if DB is empty) a sample database will be created with 2 users and 4 groups.
Use the username "j_doe" and password "dogood" to login and have access to the administration interface. 

This should be run behind a reverse proxy like nginx that handles https!

4. Point glauth to the config.cfg created by glauth-ui


### Environment Variables:

These can be set using environment variables using docker.

`SECRET_KEY=`

Should be a long random string to protect against CSRF attacks (https://flask-wtf.readthedocs.io/en/stable/form.html) and definatly set in a production environment.

`APPNAME=`

Short name that will be displayed in the webapp and emails. Default = `Glauth UI`

`ORGANISATION=`

Longer organisations name that will show up in emails. Default = `LDAP Management Team`

`ADMIN_GROUP=glauth_admin`

Name of the glauth/ldap group which members have admin access to the ui (This can't be an included/nested group atm and must be assigned directly to the user)

`FLASK_DEBUG=`

Enable Debugging mode in Flask, never enable this for production environment! Default = `False`

```
MAIL_SERVER=mail.example.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=username
MAIL_PASSWORD=password
MAIL_ADMIN=admin@example.com
```
Configure your email provider, `MAIL_ADMIN` will show up as sender. Default = `admin@example.com`

`DATABASE_URL=`

Sets the Databsae URI, Default is a sqlite `app.db` in the apps `db/` subdirectory.
For MySQL/Maria DB use `mysql+pymysql://<user>:<password>@<server>:<port>/<db>`.
See also (https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#connection-uri-format) for more Options.

`GLAUTH_CFG_PATH=`

Sets the Glauth config.cfg path, Default is `config.cfg` in the apps `db/` subdirectory.

### Usage:

coming soon...