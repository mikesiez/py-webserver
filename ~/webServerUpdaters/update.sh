#!/bin/bash
cd /home/mike/webserver || exit
git fetch origin main
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse origin/main)


if [ "$LOCAL" != "$REMOTE" ]; then
    echo "Updating server..."
    git pull origin main
    sleep 1
    date '+%Y-%m-%d %H:%M:%S' > lastupdated.txt
    sleep 0.5
    sudo systemctl restart micha-server.service
    sleep 2
    sudo systemctl restart micha-minecraft.service
else
    echo "Already up to date."
fi
