# Webserver services
## micha-server (main) & micha-minecraft for minecraft dashboard
### Runs via gunicorn that routes to local ports and those are routed outwards by nginx

# F2B
## Rate limiter for failed authentication attempts

### Test regex:
###### sudo fail2ban-regex /home/mike/webserver/logs/auth.log /etc/fail2ban/filter.d/flask-auth.conf

### List all jails and their status:
###### sudo fail2ban-client status
###### sudo fail2ban-client status flask-auth

#### If someone triggers the jail:
###### sudo fail2ban-client banned
