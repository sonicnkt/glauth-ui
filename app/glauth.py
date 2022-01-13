# Generate glauth config
from app import app
from app.models import User, Group, Settings
from time import strftime, localtime

def create_glauth_config():
    settings = Settings.query.get(1)
    users = User.query.all()
    primarygroups = Group.query.filter_by(primary=True).all()
    othergroups = Group.query.filter_by(primary=False).all()
    groups = primarygroups + othergroups
    new_config = "## GLAUTH config backend configuration file\n"
    new_config += "# Autogenerated by glauth-ui - {}\n".format(strftime("%Y-%m-%d - %H:%M:%S ", localtime()))
    new_config += "\n# General configuration\nwatchconfig = true\n"
    new_config += "debug = {}\n".format(str(settings.debug).lower())
    new_config += "\n[ldap]\n"
    new_config += "  enabled = {}\n".format(str(settings.ldap_enabled).lower())
    if settings.ldap_enabled and settings.ldap_listen:
        new_config += "  listen = \"{}\"\n".format(settings.ldap_listen)
    new_config += "\n[ldaps]\n"
    new_config += "  enabled = {}\n".format(str(settings.ldaps_enabled).lower())
    # Test what is the output if this is still null?
    if settings.ldaps_enabled and settings.ldaps_listen:
        new_config += "  listen = \"{}\"\n".format(settings.ldaps_listen)
        new_config += "  cert = \"{}\"\n".format(settings.ldaps_cert)
        new_config += "  key = \"{}\"\n".format(settings.ldaps_key)
    new_config += "\n# Backend configuration\n"
    new_config += "[backend]\n  datastore = \"config\"\n"
    new_config += "  baseDN = \"{}\"\n".format(settings.basedn)
    if settings.nameformat and (settings.nameformat != ""):
        new_config += "  nameformat = \"{}\"\n".format(settings.nameformat)
    if settings.groupformat and (settings.groupformat != ""):
        new_config += "  groupformat = \"{}\"\n".format(settings.groupformat)
    if settings.sshkeyattr and (settings.sshkeyattr != ""):
        new_config += "  sshkeyattr = \"{}\"\n".format(settings.sshkeyattr)                
    new_config += "\n\n## LDAP Users configuration\n"
    for user in users:
        new_config += "[[users]]\n"
        new_config += "  name = \"{}\"\n".format(user.username)
        if user.givenname:
            new_config += "  givenname = \"{}\"\n".format(user.givenname)
        if user.surname:
            new_config += "  sn = \"{}\"\n".format(user.surname)
        if user.mail:
            new_config += "  mail = \"{}\"\n".format(user.mail)
        new_config += "  uidnumber = {}\n".format(user.uidnumber)
        new_config += "  primarygroup = {}\n".format(user.primarygroup)
        new_config += "  passsha256 = \"{}\"\n".format(user.password_hash)
        if len(user.othergroups) > 0:
            new_config += "  otherGroups = [ {} ]\n".format(",".join(str(group.gidnumber) for group in user.othergroups))
        if not user.is_active:
            new_config += "  disabled = true\n"
        new_config += "\n"

    new_config += "## LDAP Groups configuration\n"
    for group in groups:
        new_config += "[[groups]]\n"
        new_config += "  name = \"{}\"\n".format(group.name)
        new_config += "  gidnumber = {}\n".format(group.gidnumber)
        # Need to count the query results as len() is not working here.
        if group.included_in.count() > 0:
            new_config += "  includegroups = [ {} ]\n".format(",".join(str(group.gidnumber) for group in group.included_in))
        # Add Group description as comment
        if group.description != None:
            new_config += "  # {}\n".format(group.description)
        new_config += "\n"

    f = open(app.config['GLAUTH_CFG_PATH'], "w")
    f.write(new_config)
    f.close()


