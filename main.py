import os
import discord
from discord.ext import commands
import asyncio
import random as rand
import re
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

halfHour = 1800
twoHours = 7200
sixHours = 21600
noSlowmode = halfHour

advertChannels = {
#   Server ID:              	Channel ID,           	Invites,    	Markdown,   	Emoji,   	Delay
    152517096104919042:		(296693573292916741,	False,		False,		True,		sixHours),		# Official RL Server
    677907326568628247:		(748545565243211776,	True,		True,		True,		twoHours),		# Striped
    681994761787146253:		(699019104228475004,	True,		True,		True,		noSlowmode),	# Uuest
#    1061789478508843109:	(1074743282212544643,	False,		False,		True,		noSlowmode),		# Yota (Need lvl 3 to promo) (Server promo not allowed)
    689614991770517517:		(715709356796280832,	True,		True,		True,		sixHours),		# CBell
    489971613312221214:		(519668945930813440,	False,		True,		False,		halfHour),		# Musty (Phone verification required)
    303678101726953473:		(333234568188526592,	False,		True,		True,		halfHour),		# Sunless
    826570781512957953:		(950792225648934932,	True,		True,		True,		sixHours),		# Calvin
    184316748714082304:		(184317694957322240,	False,		True,		False,		sixHours),		# Mertzy
    456876324590452746:		(705162339850125372,	True,		True,		True,		sixHours),		# Wayton
    300815426462679051:		(493507781975080990,	False,		True,		True,		sixHours),		# Sledge
    455404871890370561:		(646803117312049162,	False,		True,		True,		sixHours),		# Lethamyr (Phone verification required)
    619603099975286814:		(651362001720836105,	True,		True,		True,		sixHours),		# Rocket Lounge
}
RLServers = set(advertChannels.keys())

def advert(invites: bool, markdown: bool, emoji: bool):
	return f"""{"# 🌟 __Havic Gaming__ 🌟" if emoji and markdown else ("🌟 **__Havic Gaming__** 🌟" if emoji else ("# __Havic Gaming__" if markdown else "**__Havic Gaming__**"))}

{"## __Who are we?__" if markdown else "__**Who are we?**__"}
‣ We are a small, but growing, rocket league organization in the competitive scene made so you can meet new people and find a team for you to compete in leagues with.

{"## What do we offer?" if markdown else "**What do we offer?**"}
{"> `🤗`" if emoji and markdown else ("🤗" if emoji else ("> " if markdown else ""))} ‣ A nice, welcoming and non-toxic community
{"> `👨‍🏫`" if emoji and markdown else ("👨‍🏫" if emoji else ("> " if markdown else ""))} ‣ Chance for __**free coaching**__ from a Top 1% Player in multiple game modes
{"> `🏆`" if emoji and markdown else ("🏆" if emoji else ("> " if markdown else ""))} ‣ Fun and friendly __**tournaments**__ between other community members and other orgs! (WIP)
{"> `🎉`" if emoji and markdown else ("🎉" if emoji else ("> " if markdown else ""))} ‣ Occasional __**giveaways for free nitro**__ and more!
{"> `6️⃣`" if emoji and markdown else ("6️⃣" if emoji else ("> " if markdown else ""))} ‣ Server exclusive __**6mans**__
{"> `🎨`" if emoji and markdown else ("🎨" if emoji else ("> " if markdown else ""))} ‣ Plenty of roles to set yourself out from your friends and compete for a variety of positions
{"> `📈`" if emoji and markdown else ("📈" if emoji else ("> " if markdown else ""))} ‣ A place to grow as a player in the competitive scene
{"> `🧑‍🤝‍🧑`" if emoji and markdown else ("🧑‍🤝‍🧑" if emoji else ("> " if markdown else ""))} ‣ A nice place to hangout and make friends

{"## __Requirements__" if markdown else "__**Requirements**__"}
‣ None!
  You don't even have to play rocket league, you can join just to chat with people and have fun.
‣ If you are looking to be a player in our org, just join and open an LFT ticket and we'll let you know when we've found a team for you

{"https://discord.gg/v88Bj6FFjR" if invites else ("## DM me for more info!" if markdown else "**DM me for more info!**")}
"""

@bot.event
async def on_ready():
    logging.info(f'{YELLOW}Logged in as{RESET} {bot.user}{YELLOW}\n----------------------------\n{RESET}')
    bot.loop.create_task(periodic_advert_task())  # Start periodic task
    logging.info(f'{YELLOW}Started periodic advert task{RESET}')

async def send_advert(channel, guild_id, allows_invites, allows_markdown, allows_emojis):
	# Check for a delay based on the slowmode and time since the last message sent
	last_message_time = None
	try:
		async for last_message in channel.history(limit=30):
			if last_message.author == bot.user:  # Ensure message is sent by bot
				last_message_time = last_message.created_at.replace(tzinfo=timezone.utc)
				break
	except Exception as e:
		logging.error(f"{RED}Failed to fetch last message for slow mode check:{RESET} {e}")

	# Check if slowmode or time delay
	cooldown_expiration = None
	if last_message_time:
		cooldown_expiration = last_message_time + timedelta(seconds=channel.slowmode_delay)
		if datetime.now(timezone.utc) < cooldown_expiration:
			cooldown_expiration_cet = cooldown_expiration.astimezone(cet)
			logging.warning(f"{RED}Skipping{RESET} {guild_id}{RED} due to active slow mode. Next message allowed at{RESET} {cooldown_expiration_cet.strftime('%Y-%m-%d %H:%M:%S %Z')}{RED}.{RESET}")
			return

	# Apply a minimum 30 minute gap before sending the advert again
	current_time = datetime.now(timezone.utc)
	delay = noSlowmode if guild_id in advertChannels else halfHour
	if last_message_time and current_time - last_message_time < timedelta(seconds=delay):
		next_allowed_time = last_message_time + timedelta(seconds=delay)
		next_allowed_time_cet = next_allowed_time.astimezone(cet)
		logging.warning(f"{RED}Skipping {RESET}{guild_id}{RED} due to delay. Next message allowed at {RESET}{next_allowed_time_cet.strftime('%Y-%m-%d %H:%M:%S %Z')}{RED}.{RESET}")
		return

	# Before sending the new advert, delete the previous adverts
	try:
		bot_messages = [msg async for msg in channel.history(limit=30) if msg.author == bot.user]
		for message in bot_messages:
			if message.content == advert(allows_invites, allows_markdown, allows_emojis):
				await message.delete()
				logging.info(f"{GREEN}Deleted a previous advert message sent by the bot in{RESET} {guild_id}{GREEN}.{RESET}")

				# Send the new advert
				try:
					await channel.send(advert(allows_invites, allows_markdown, allows_emojis))
					logging.info(f"{GREEN}Sent advert to {RESET}{guild_id}{GREEN} in {RESET}{channel}{GREEN}.{RESET}")
				except discord.HTTPException as e:
					logging.error(f"{RED}Failed to send advert:{RESET} {e}{RED}.{RESET}")

	except discord.HTTPException as e:
		logging.error(f"{RED}Failed to fetch messages for deletion:{RESET} {e}{RED}{RESET}")

async def send_dms(user, message):
	retry_delay = 5
	while True:
		try:
			UIDRegex = r"(\b\d{17,19}\b|<@!?\d{17,19}>)"
			cleanMessage = re.sub(UIDRegex, "", message.content, count=1).strip()
			await user.send(f"{message.author} ({message.author.id}) messaged {user.name}:\n```{cleanMessage}```")
			return
		except discord.HTTPException as e:
			logging.error(f"{RED}Rate limit hit! Retrying in{RESET} {retry_delay}{RED} sec...{RESET} {e}{RESET}")
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
		UIDRegex = r"(\b\d{17,19}\b|<@!?\d{17,19}>)"
		user = re.search(UIDRegex, message.content)

		if user:
			if message.author.id in [1022513154623811655, 178939117420281866]:
				userID = user.group(1)  # Extract matched User ID or mention
				userID = re.sub(r"\D", "", userID)  # Remove non-numeric characters
				user = bot.get_user(int(userID))

				if not user:
					logging.warning(f"{RED}Failed to fetch user with ID {RESET}{userID}{RED}.{RESET}")
					return
				
				# Remove all User IDs or mentions
				cleanMessage = re.sub(UIDRegex, "", message.content, count=1).strip()

				if cleanMessage:
					await user.send(cleanMessage)
					logging.info(f"{GREEN}Relayed DM from{RESET} {message.author}{GREEN} to{RESET} {user.name}({user.id}){GREEN}:{RESET}\n{cleanMessage}")

					brad = bot.get_user(1022513154623811655)
					await send_dms(brad, message)

					crum = bot.get_user(178939117420281866)
					await send_dms(crum, message)

					logging.info(f"{GREEN}Relayed response to crummei and bradley:{RESET}\n{cleanMessage}")

				else:
					await message.channel.send("Message included only a recipient.")
					logging.info(f"{YELLOW}Received only recipient for relay.{RESET}")

		else:
			brad = bot.get_user(1022513154623811655)
			await send_dms(brad, message)

			crum = bot.get_user(178939117420281866)
			await send_dms(crum, message)

			logging.info(f"{GREEN}Relayed DM to crummei and bradley:{RESET}\n{message.content}")

async def send_advert_periodically(guild_id, channel_id, allows_invites, allows_markdown, allows_emojis, delay):
	while True:
		channel = bot.get_channel(channel_id)
		if channel:
			await sendMessage(
				type='adverts',
				message=None,
				channel=channel,
				guild_id=guild_id,
				allows_invites=allows_invites,
				allows_markdown=allows_markdown,
				allows_emojis=allows_emojis
			)
		await asyncio.sleep(delay)

async def periodic_advert_task():
    for guild_id, (channel_id, allows_invites, allows_markdown, allows_emojis, delay) in advertChannels.items():
        bot.loop.create_task(send_advert_periodically(guild_id, channel_id, allows_invites, allows_markdown, allows_emojis, delay))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if not message.guild:  # Handle DMs
        await sendMessage(type="dms", message=message, channel=message.channel)
        return

bot.run(os.environ.get('TOKEN'))
