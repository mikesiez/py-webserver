import flask
import subprocess
import threading
import json
import os
import time
import gevent # module required to asssure asynchornous and non-blocking behaviour from tasks such as the while loop that streams logs. this'll make it be ran side by side by other requests bc we're using gevent in gunicorn
import asyncio
import websockets
from dotenv import load_dotenv
from flask_session import Session

load_dotenv()

STATE_FILE = "/home/mike/mcServers/minecraft_state.json"
MC_DIR = "/home/mike/mcServers/ats10-mcserver"
MAX_LOG_LINES = 200

minecraft_process = None
minecraft_logs = []
minecraft_lock = threading.Lock()
plrsInServer = []
timeStampTracker = [False,False,False,False,False] # 5 hours, 10 hours, 15 hours, 16 hours

app = flask.Flask(__name__)
# Use same secret & session type/dir as main app so they are linked
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config['SESSION_TYPE'] = os.getenv("FLASK_SESSION_TYPE")
app.config['SESSION_FILE_DIR'] = os.getenv("FLASK_SESSION_DIR")
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)  # initialize server-side sessions

startTime = time.time()

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"status": "stopped"}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    post_discord_message('Server state switched to '+state['status'])
    change_rpc()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def run_async(coro): # running coroutines and queuing reqs in running async loop for following 2 funcs
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)
        return

    asyncio.run_coroutine_threadsafe(coro, loop)

def post_discord_message(msg):
    async def message():
        async with websockets.connect('ws://127.0.0.1:8765') as ws:
            await ws.send(msg)

    threading.Thread(target=lambda: run_async(message()), daemon=True).start()

def change_rpc():
    async def send():
        async with websockets.connect('ws://127.0.0.1:8765') as ws:
            await ws.send(f'BOT_CHANGE_RPC{len(plrsInServer)}')

    threading.Thread(target=lambda: run_async(send()), daemon=True).start()


def stream_logs(proc):
    """Read Minecraft stdout and push to shared log list."""
    global minecraft_logs, plrsInServer, timeStampTracker
    for line in proc.stdout:
        line = line.rstrip()
        with minecraft_lock: # avoid race condition / conflic with streamer function
            minecraft_logs.append(line)
            if len(minecraft_logs) > MAX_LOG_LINES:
                minecraft_logs = minecraft_logs[-MAX_LOG_LINES:]

        now = time.time()

        if now - startTime >= 60000 and timeStampTracker[4] == False:
            timeStampTracker[4] = True
            post_discord_message(f'Machine has been on for >17 hours [RECOMMENDED RESTART OVERDUE ⚠️]. Players online: {len(plrsInServer)}')
        elif now - startTime >= 57600 and timeStampTracker[3] == False:
            timeStampTracker[3] = True
            post_discord_message(f'Machine has been on for 16 hours [MACHINE RESTART RECOMMENDED]. Players online: {len(plrsInServer)}')
        elif now - startTime >= 54000 and timeStampTracker[2] == False:
            timeStampTracker[2] = True
            post_discord_message(f'Machine has been on for 15 hours [RESTART RECOMMENDED IN 1 HOUR]. Players online: {len(plrsInServer)}')
        elif now - startTime >= 36000 and timeStampTracker[1] == False:
            timeStampTracker[1] = True
            post_discord_message(f'Machine has been on for 10 hours. Players online: {len(plrsInServer)}')
        elif now - startTime >= 18000 and timeStampTracker[0] == False:
            timeStampTracker[0] = True
            post_discord_message(f'Machine has been on for 5 hours. Players online: {len(plrsInServer)}')

        # if we ever get problem here could be race condition wrap this in with minecraft_lock:
        if "Done (" in line:
            state = load_state()
            state["status"] = "running"
            save_state(state)

        elif "UUID of player" in line:
            output = line.split()
            name = output[8]
            UUID = output[-1]
            if name not in plrsInServer:
                plrsInServer.append(name)
            post_discord_message(f"User joined server: {name} | Players online: {len(plrsInServer)}")
            change_rpc()

        elif "left the game" in line:
            output = line.split()
            name = output[-4]
            if name in plrsInServer:
                plrsInServer.remove(name)
            post_discord_message(f"User left server: {name} | Players online: {len(plrsInServer)}")
            change_rpc()

        elif "has made the advancement" in line:
            output = line.split()
            advancement = " ".join(output[9:])
            playerWhoGot = output[4]
            post_discord_message(f"{playerWhoGot} got achievement {advancement}")

    # After process exits
    state = load_state()
    if state.get("status") == "stopping":
        with minecraft_lock:
            minecraft_logs.append("[Server stopped]")
            if len(minecraft_logs) > MAX_LOG_LINES:
                minecraft_logs = minecraft_logs[-MAX_LOG_LINES:]
        state["status"] = "stopped"
        save_state(state)
        subprocess.run(
            ["/bin/bash", "/home/mike/mcServers/autoBPs/runManualBP.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )


def require_login():
    if not flask.session.get('authenticated') or not flask.session.get('username') in ['michael','ats10']:
        return flask.redirect("/login")


def minecraft_page():
    login_check = require_login()
    if login_check:
        return login_check

    user = flask.session.get('username')
    try:
        user = str(user).upper()
    except:
        user = "err"

    return flask.render_template("minecraft.html",user=user)

def minecraft_action():
    global minecraft_process
    global minecraft_logs

    secret_key = os.getenv('BOT_API_KEY')

    if flask.request.headers.get('X-BOT-SECRET') == secret_key:
        print('do bot things')
    else:
        login_check = require_login()
        if login_check:
            return login_check

    action = flask.request.args.get("action")
    cmd_text = flask.request.args.get("cmd", "").strip()

    restricted_cmds = ["stop"]

    state = load_state()
    status = state.get("status", "stopped")

    with minecraft_lock:
        if action == "start":
            if status != "stopped":
                return {"status": status}

            try:
                minecraft_process = subprocess.Popen(
                    ["/bin/bash", f"{MC_DIR}/run.sh"],
                    cwd=MC_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                threading.Thread(target=stream_logs, args=(minecraft_process,), daemon=True).start()
                state["status"] = "booting"
                save_state(state)
                return {"status": state["status"]}
            except Exception as e:
                state["status"] = "stopped"
                save_state(state)
                return {"error": str(e)}, 500

        elif action == "stop" or (cmd_text and cmd_text.lower() == "stop"):
            if status != "running":
                return {"status": status}
            try:
                if minecraft_process:
                    minecraft_process.stdin.write("stop\n")
                    minecraft_process.stdin.flush()
                state["status"] = "stopping"
                save_state(state)
                return {"status": state["status"]}
            except Exception as e:
                return {"error": str(e)}, 500

        elif action == "status":
            return {"status": status}

        elif action == "logs":
            # return a copy of logs
           return {"logs": [line for _, line in minecraft_logs]}

        elif action == "command" and cmd_text and cmd_text not in restricted_cmds:
            if status != "running":
                return {"status": status}
            try:
                if minecraft_process:
                    minecraft_process.stdin.write(cmd_text + "\n")
                    minecraft_process.stdin.flush()
                with minecraft_lock:
                    minecraft_logs.append(f"[Command sent]: {cmd_text}")
                    if len(minecraft_logs) > MAX_LOG_LINES:
                        minecraft_logs = minecraft_logs[-MAX_LOG_LINES:]
                return {"status": f"Sent command: {cmd_text}"}
            except Exception as e:
                return {"error": str(e)}, 500

        elif action == 'reset':
            if status != "stopped":
                state["status"] = "stopped"
                save_state(state)
                return {"status":"stopped"}
            return {"status": status}

        elif action == 'manualSet':
            state['status'] = cmd_text
            save_state(state)
            return {'status': status}
        else:
            return {"error": "Invalid action"}, 400

def minecraft_stream():
    if require_login():
        return require_login()

    def generate():
        last_sent = []
        last_status = None
        while True:
            try:
                lines_to_send = []
                with minecraft_lock: # avoid race condition / conflic with logger function
                    lines_to_send=minecraft_logs.copy()  # pop from front

                if lines_to_send != last_sent:
                    for line in lines_to_send:
                        yield f"event: log\ndata: {line}\n\n"
                    last_sent = lines_to_send.copy()

                # Send status updates if changed
                state = load_state()
                current_status = state.get("status")
                if current_status != last_status:
                    yield f"event: status\ndata: {current_status}\n\n"
                    last_status = current_status

                gevent.sleep(0.5)

            except GeneratorExit:
                print("[minecraft_stream] Client disconnected cleanly.")
                break
            except Exception as e:
                print(f"[minecraft_stream] Stream error: {e}")
                gevent.sleep(1)

    return flask.Response(generate(), mimetype="text/event-stream")


# --- Routes ---
app.add_url_rule("/minecraft", "minecraft_page", minecraft_page)
app.add_url_rule("/minecraft/action", "minecraft_action", minecraft_action, methods=["GET", "POST"])
app.add_url_rule("/minecraft/stream",'minecraft_stream',minecraft_stream, methods=['GET'])

def launch_disc_bot():
    time.sleep(15) # wait for wifi
    subprocess.Popen(
        ["/home/mike/webserver/launch_bot.sh"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    time.sleep(10) # wait for bot startup
    state = load_state()
    if state.get("status") != "stopped":
        state['status'] = 'CRASHED OR INCORRECTLY POWERED OFF.'
        save_state(state)
    else:
        post_discord_message('Machine restarted, server ready to be launched.')
        change_rpc()

launch_disc_bot()

if __name__ == "__main__": # this doesnt actually run, gunicorn runs this module in a way that doesnt utilize this so app.run isnt actually running here. and the port and ip info is what we gave in the exec in the service as --bind.
    app.run(host="127.0.0.1", port=5001, debug=False)
