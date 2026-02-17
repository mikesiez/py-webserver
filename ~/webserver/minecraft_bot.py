from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import websockets
import requests
import os
import logging
import json

load_dotenv()
logging.getLogger('discord').setLevel(logging.WARNING)

STATE_FILE = "/home/mike/mcServers/minecraft_state.json"
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"status": "stopped"}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

async def handler(ws):
    async for message in ws:
        if "BOT_CHANGE_RPC" in message:
            num = 0
            try:
                num = int(message.strip()[-1])
            except:
                try:
                    num = int(message.strip()[-2:])
                except:
                    num = 0
            await change_rpc(num)
        else:
            await post_discord_message(message.strip())

async def start_websocket():
    async with websockets.serve(handler, "127.0.0.1", 8765):
        await asyncio.Future()


token = os.getenv('DISC_BOT_TOKEN')
LOG_CHANNEL_IDs = [1433481421984628866,1436354083043672167]
#Testing_LOG_CHANNEL_ID = 1423766293223313409

intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def post_discord_message(content):
    if os.getenv('TESTING') == "True": # we're testing and not in testing channel 
        return
    
    for LOG_CHANNEL_ID in LOG_CHANNEL_IDs:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        await channel.send(content)


flask_action_endpoint = "http://127.0.0.1:5001/minecraft/action"
secret_key = os.getenv('BOT_API_KEY')

async def start_server_cmd(interaction: discord.Interaction):
    state = load_state()
    status = state.get("status")

    if status != "stopped":    
        await interaction.response.send_message(
            f"Could not start server, current state: {status}. Is the server already running?"
        )
        return
    try:
        r = requests.post(
            f"{flask_action_endpoint}?action=start",
            headers={'X-BOT-SECRET':secret_key}
        )
        await interaction.response.send_message(
            f"Server launch commenced. State: {r.json().get('status')} | ~40s estimated until launch complete. "
            f"See #server-logs for more information."
        )
    except:
        await interaction.response.send_message("err")


async def stop_server_cmd(interaction: discord.Interaction):
    state = load_state()
    status = state.get("status")

    if status != "running":    
        await interaction.response.send_message(
            f"Could not stop server, current state: {status}. Is the server already off?"
        )
        return

    try:
        r = requests.post(
            f"{flask_action_endpoint}?action=stop",
            headers={'X-BOT-SECRET':secret_key}
        )
        await interaction.response.send_message(
            f"Server stop initiated. State: {r.json().get('status')} | ~10s estimated until stopping complete. "
            f"See #server-logs for more information."
        )
    except:
        await interaction.response.send_message('sum ting wong')

"""
f"Server stop initiated. State: {r.get('status')} | ~10s estimated until stopping complete. "
        f"See <#{LOG_CHANNEL_ID}> for more information."

await interaction.response.send_message(
        f"Server launch commenced. State: {r.get('status')} | ~1m estimated until launch complete. "
        f"See <#{LOG_CHANNEL_ID}> for more information."
)
"""

# Register slash commands manually
bot.tree.add_command(app_commands.Command(
    name="start",
    description="Start the Minecraft server",
    callback=start_server_cmd
))

bot.tree.add_command(app_commands.Command(
    name="stop",
    description="Stop the Minecraft server",
    callback=stop_server_cmd
))


async def change_rpc(plrNum=0):
    state = load_state()
    status = state.get('status')

    if status == 'running':
        fillin = f"Running: {plrNum} players online."
    else:
        fillin = f"Status: {status}"

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"ATM10 - {fillin}"
    )

    await bot.change_presence(activity=activity)


async def on_ready():
    print(f"Discord bot connected as {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash commands synced globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    await change_rpc()

bot.add_listener(on_ready, "on_ready")

async def run_global():

    await asyncio.gather(
        start_websocket(),
        bot.start(token)
    ) # so the async apps run within a same asyncio loop
    
# Run directly if this script is executed
if __name__ == "__main__":
    asyncio.run(run_global())
    
    