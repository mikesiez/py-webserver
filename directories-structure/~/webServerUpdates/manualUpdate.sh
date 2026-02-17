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
else
    echo "Already up to date."
fi
