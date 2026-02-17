# F2B
### Test regex:
###### sudo fail2ban-regex /home/mike/webserver/logs/auth.log /etc/fail2ban/filter.d/flask-auth.conf

### List all jails and their status:
###### sudo fail2ban-client status
###### sudo fail2ban-client status flask-auth

#### If someone triggers the jail:
###### sudo fail2ban-client banned
