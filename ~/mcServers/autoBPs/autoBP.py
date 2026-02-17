import shutil
import os
import datetime
import requests
import json
import random

sName = "ats10-mcserver"
mcdir = "/home/mike/mcServers"
backupDir = mcdir+"/backup"
serverFolder = mcdir+f'/{sName}'
stateFilePath = mcdir+"/minecraft_state.json"

def listBackups():
    amt = 0
    List = []
    for file in os.listdir(backupDir):
        amt += 1
        try:
            lastupd = open(f"{backupDir}/{file}/backupdate.txt",'r').read().strip()
        except:
            lastupd = "Unknown"

        List.append(f"{amt} - Backup date: {lastupd}")

    return(List)

def manageBackup():
    with open(stateFilePath, "r") as f:
        state = json.load(f).get('status')

    if state != 'running':
        return

    latestVer = 0
    lowestActiveBp = 999999
    numOfBPs = 0
    for file in os.listdir(backupDir):
        numOfBPs+=1
        tripleD = int(file[-6:])
        if tripleD > latestVer:
            latestVer = tripleD
        if tripleD < lowestActiveBp:
            lowestActiveBp = tripleD

    def turntoTriple(num:int):
        strN = str(num)
        while len(strN) < 6:
            strN = "0"+strN
        return strN

    def createBP():
        newNum = turntoTriple(latestVer+1)
        shutil.copytree(serverFolder,backupDir+f"/{sName+newNum}")
        f = open(backupDir+f"/{sName+newNum}/backupdate.txt",'w')
        f.write(str(datetime.datetime.now())[:-7])
        f.close()

    if numOfBPs == 5:
        toRem = f"{backupDir}/{sName+turntoTriple(lowestActiveBp)}"
        shutil.rmtree(toRem)
    createBP()
    print('success')

    def post_results():
        print('posted')
        bps = listBackups()
        webhook_url = "https://discord.com/api/webhooks/1434391774733795461/XjrKId3aNaf9gusXVH0n8mYbixz6v0IBPuLZLGguWz-pUjVEkvdvTf4R9vJaCRhmCOPq"
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

        payload = {
            "content": None,
            "embeds": [
                {
                    "title": "",
                    "description": "Current backups:\n"+"\n".join(bps),
                    "color": 3386627,
                    "author": {
                        "name": "Successfully backed up server files",
                        "icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Refresh_icon.svg/1200px-Refresh_icon.svg.png"
                    },
                    "footer":{"text":"Backups every 15m"},
                    "timestamp": current_time
                }
            ],
            "username": "backup-logs",
            "avatar_url": "https://cdn.discordapp.com/icons/1324883011778510938/6a1fef43f9146fb1363014fad0a6e693.png?size=100&quality=lossless",
            "attachments": []
        }

        response = requests.post(webhook_url, json=payload)

    if random.randint(1,6) == 3:
        post_results()


manageBackup()
