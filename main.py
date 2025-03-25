import os
import discord
from discord.ext import commands
import asyncio
import random as rand
from datetime import datetime, timedelta, timezone
import pytz
cet = pytz.timezone("Europe/Copenhagen")
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from flask import Flask
import threading
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

thread = threading.Thread(target=run_flask)
thread.start() 

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

bot = commands.Bot(command_prefix='crum!', self_bot=False)

bot.advertGaps = {}
bot.timers = {}
halfHour = 1800
twoHours = 7200
sixHours = 21600
noSlowmode = halfHour

advertChannels = {
#   Server ID:              Channel ID,             Invites,    Markdown,   Emoji,   	Delay
    152517096104919042:		(296693573292916741,	False,		True,		True,		sixHours),		# Official RL Server
    677907326568628247:		(748545565243211776,	True,		True,		True,		twoHours),		# Striped
    681994761787146253:		(699019104228475004,	True,		True,		True,		noSlowmode),	# Uuest
#    1061789478508843109:	(1074743282212544643,	False,		False,		True,		noSlowmode),	# Yota (Need lvl 3 to promo) (Server promo not allowed)
    689614991770517517:		(715709356796280832,	True,		True,		True,		sixHours),		# CBell
    489971613312221214:		(519668945930813440,	False,		True,		False,		halfHour),		# Musty (Phone verification required)
    303678101726953473:		(333234568188526592,	False,		True,		True,		halfHour),		# Sunless
    826570781512957953:		(950792225648934932,	True,		True,		True,		sixHours),		# Calvin
    184316748714082304:		(184317694957322240,	False,		True,		False,		sixHours),		# Mertzy
    456876324590452746:		(705162339850125372,	True,		True,		True,		sixHours),		# Wayton
    300815426462679051:		(493507781975080990,	False,		True,		True,		sixHours),		# Sledge
    455404871890370561:		(646803117312049162,	False,		True,		True,		noSlowmode),	# Lethamyr (Phone verification required)
    619603099975286814:		(651362001720836105,	True,		True,		True,		sixHours),		# Rocket Lounge
}
RLServers = set(advertChannels.keys())

def advert(invites: bool, markdown: bool, emoji: bool):
    return f"""# 🌟 __Havic Gaming__ 🌟

{"## Who are we?" if markdown else "**Who are we?**"}
- We are a small, but growing, rocket league organization in the competitive scene made so you can meet new people and find a team for you to compete in leagues with.

{"## What do we offer?" if markdown else "**What do we offer?**"}
-{" 🤗 " if emoji else " "}A nice, welcoming and non-toxic community
-{" 👨‍🏫 " if emoji else " "}Chance for free coaching from a Top 1% Player in multiple game modes
-{" 🏆 " if emoji else " "}Fun and friendly tournaments between other community members and other orgs! (WIP)
-{" 🧑‍🤝‍🧑 " if emoji else " "}A nice place to hangout and make friends
-{" 6️⃣ " if emoji else " "}Server exclusive 6mans
-{" 🎨 " if emoji else " "}Plenty of roles to set yourself out from your friends and compete for a variety of positions
-{" 📈 " if emoji else " "}A place to grow as a player in the competitive scene

{"## Requirements" if markdown else "**Requirements**"}
- None!
- You don't even have to play rocket league, you can join just to chat with people and have fun.
- If you are looking to be a player in our org, just join and open an LFT ticket and we'll let you know when we've found a team for you

{"https://discord.gg/v88Bj6FFjR" if invites else ("## DM me for more info!" if markdown else "**DM me for more info!**")}
"""

@bot.event
async def on_ready():
    logging.info(f'{YELLOW}Logged in as {bot.user}{RESET}\n----------------------------\n')
    # Ensure both attributes are initialized as empty if there are no connected guilds
    bot.advertGaps = {guild.id: rand.randint(2, 4) for guild in bot.guilds if guild.id in RLServers}
    bot.timers = {guild.id: False for guild in bot.guilds if guild.id in RLServers}
    logging.info(f'{YELLOW}Initialized gaps:{RESET} {bot.advertGaps}\n')
    logging.info(f'{YELLOW}Initialized timers:{RESET} {bot.timers}\n')
    await send_adverts_on_startup()
    await start_all_timers()


async def send_advert(channel, guild_id, allows_invites, allows_markdown, allows_emojis):
    retry_delay = 5

    # Check if the delay timer is still active
    if bot.timers.get(guild_id, False):
        logging.info(f"{RED}Skipping {guild_id} because the delay timer is still active.{RESET}")
        return

    # Check for slow mode
    if channel.slowmode_delay > 0:
        try:
            last_message = await anext(channel.history(limit=1).__aiter__(), None)

            if last_message:
                last_message_time = last_message.created_at.replace(tzinfo=timezone.utc)
                cooldown_expiration = last_message_time + timedelta(seconds=channel.slowmode_delay)

                if datetime.now(timezone.utc) < cooldown_expiration:
                    cooldown_expiration_cet = cooldown_expiration.astimezone(cet)
                    logging.info(f"{RED}Skipping {guild_id} due to active slow mode. Next message allowed at {cooldown_expiration_cet.strftime('%Y-%m-%d %H:%M:%S %Z')}.{RESET}")
                    bot.timers[guild_id] = False
                    return
        except discord.HTTPException as e:
            logging.info(f"{RED}Failed to fetch last message for slow mode check:{RESET} {e}")
            return
    else:
        # Delete the last 3 messages sent by the bot in the channel
        try:
            bot_messages = [msg async for msg in channel.history(limit=10) if msg.author == bot.user][:3]
            if len(bot_messages) < 3:
                logging.info(f"{GREEN}Less than 3 messages from the bot found, deleting all found messages in {RESET}{guild_id}{GREEN}.{RESET}")
                
            for msg in bot_messages:
                await msg.delete()
                
            logging.info(f"{GREEN}Deleted the last {RESET}{len(bot_messages)}{GREEN} messages sent by the bot in {RESET}{guild_id}{GREEN}.{RESET}")
            
        except discord.HTTPException as e:
            logging.info(f"{RED}Failed to delete previous messages in {RESET}{guild_id}{GREEN}:{RESET} {e}")


    # Send the advert message
    while True:
        try:
            await channel.send(advert(allows_invites, allows_markdown, allows_emojis))
            logging.info(f"{GREEN}Sent advert to {guild_id} in {channel}{RESET}")
            return
        except discord.Forbidden:  # Missing permissions (HTTP 403)
            logging.error(f"{RED}Missing Permissions in guild {guild_id}, skipping to the next server.{RESET}")
            return
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limit hit
                retry_after = int(e.response.headers.get("Retry-After", 5))
                logging.warning(f"{RED}Rate limit hit! Retrying after {retry_after} seconds...{RESET}")
                await asyncio.sleep(retry_after)
            else:
                logging.error(f"{RED}HTTP Error: {e}{RESET}")



async def send_dms(channel, message):
    retry_delay = 5
    while True:
        try:
            await channel.send(f'{message.author} said:\n```{message.content}```')
            return
        except discord.HTTPException as e:
            logging.info(f"{RED}Rate limit hit! Retrying in{RESET} {retry_delay}{RED} sec...{RESET} {e}")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)

async def sendMessage(type, message, channel, **kwargs):
    if type == "adverts":
        # Get guild flags
        guild_id = kwargs.get("guild_id", False)
        allows_invites = kwargs.get("allows_invites", False)
        allows_markdown = kwargs.get("allows_markdown", False)
        allows_emojis = kwargs.get("allows_emojis", False)
        await send_advert(channel, guild_id, allows_invites, allows_markdown, allows_emojis)

    elif type == "dms":
        brad = bot.get_user(1022513154623811655)
        crum = bot.get_user(178939117420281866)

        await send_dms(brad, message)
        logging.info(f"{GREEN}Relayed DM to bradley")
        await send_dms(crum, message)
        logging.info(f"{GREEN}Relayed DM to crummei")
    
async def send_adverts_on_startup():
    for guild_id, (channel_id, allows_invites, allows_markdown, allows_emojis, *_) in advertChannels.items():
        channel = bot.get_channel(channel_id)
        await asyncio.sleep(5)
        if channel:
            await send_advert(channel, guild_id, allows_invites, allows_markdown, allows_emojis)
            await asyncio.sleep(10)

async def start_timer(message, channel, guild_id):
    if guild_id not in advertChannels:
        return
    
    if isinstance(message, int):
        delay = message
    else:
		delay = (
	    advertChannels[guild_id][4] + (
		rand.randint(10, 120) if advertChannels[guild_id][4] in {halfHour, noSlowmode} else
		rand.randint(60, 300) if advertChannels[guild_id][4] == twoHours else
		rand.randint(180, 900) if advertChannels[guild_id][4] == sixHours else
		(logging.info("Failed to retrieve delay or delay not valid. Defaulting to highest value.") or rand.randint(180, 900))
	    	)
		)
    logging.info(
    f"{YELLOW}Starting delay for{RESET} {guild_id}{YELLOW}:{RESET} "
    f"{(delay // 60) if delay // 60 < 60 else (delay // 3600)}"
    f"{YELLOW} {'minutes' if delay // 60 < 60 else 'hours'}{RESET}"
    )
	
    await asyncio.sleep(delay)
    bot.timers[guild_id] = False
    channel_id, allows_invites, allows_markdown, allows_emojis, *_ = advertChannels[guild_id]
    channel = bot.get_channel(channel_id)
    
    if channel:
        await sendMessage(type='adverts', message=message, channel=channel, 
                          guild_id=guild_id, allows_invites=allows_invites, 
                          allows_markdown=allows_markdown, allows_emojis=allows_emojis)
    bot.advertGaps[guild_id] = rand.randint(2, 4)

async def start_all_timers():
    for guild_id, (channel_id, allows_invites, allows_markdown, allows_emojis, *_) in advertChannels.items():
        delay = (advertChannels[guild_id][4] + (
		rand.randint(10, 120) if advertChannels[guild_id][4] in {halfHour, noSlowmode} else
		rand.randint(60, 300) if advertChannels[guild_id][4] == twoHours else
		rand.randint(180, 900) if advertChannels[guild_id][4] == sixHours else
		(logging.info("Failed to retrieve delay or delay not valid. Defaulting to highest value.") or rand.randint(180, 900))
	    	)
		)
        channel = bot.get_channel(channel_id)
        if not bot.timers.get(guild_id, False) and channel:
            bot.timers[guild_id] = True
            asyncio.create_task(start_timer(None, channel, guild_id))



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    channel = message.channel.id
    if not message.guild:
        await sendMessage(type="dms", message=message, channel=channel)
    
    else:  
        guild_id = message.guild.id
        if guild_id not in RLServers:
            return
        if guild_id not in bot.advertGaps:
            bot.advertGaps[guild_id] = rand.randint(2, 4)
        bot.advertGaps[guild_id] -= 1
        if bot.advertGaps[guild_id] <= 0 and not bot.timers.get(guild_id, False):
            bot.timers[guild_id] = True
            asyncio.create_task(start_timer(message, channel, guild_id))
            
bot.run(os.environ.get('HAVIC'))
