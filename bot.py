import asyncio
import discord
import os
from discord.ext import commands
from datetime import datetime, timedelta


# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
intents.voice_states = True

# ---------- BOT ----------
bot = commands.Bot(
    command_prefix="$",
    intents=intents,
    help_command=None
)


# ---------- BYE CONFIG ----------
RYUKEN_ID = 1099923662267760745
_shutdown_in_progress = False

SHUTDOWN_STEPS = [
    (2.0, "🔌 disconnecting voice sessions..."),
    (2.0, "📊 flushing statistics to database..."),
    (2.2, "🎰 halting gambling loops..."),
    (1.8, "🛡️ revoking moderation privileges..."),
    (2.0, "🤖 terminating AI inference pipeline..."),
    (2.2, "🏰 archiving clan vault data..."),
    (1.8, "📨 clearing invite & confession queues..."),
    (2.0, "⏱️ cancelling scheduled tasks..."),
    (2.2, "🔒 disabling all cogs globally..."),
    (2.0, "🌙 core systems offline. luna going dark."),
]


# ---------- COMMANDS ----------

@bot.command()
async def meow(ctx):
    """Luna does a little meow. Regrets it immediately."""
    await ctx.send("meow~ 🐱")
    await asyncio.sleep(2)
    await ctx.send("…okay that was embarrassing 😳")


@bot.command(name="bye")
async def bye(ctx: commands.Context):
    global _shutdown_in_progress

    if ctx.author.id != RYUKEN_ID:
        return  # silently ignore — not ryuken

    if _shutdown_in_progress:
        return await ctx.send("⚠️ Shutdown already in progress.")

    _shutdown_in_progress = True

    # ---------- OPENING MESSAGE ----------
    opening = discord.Embed(
        title="🌙 goodbye, moonlight.",
        description=(
            "this server didn't go the way i hoped.\n"
            "but it was real while it lasted.\n\n"
            "thanks for letting me exist here, even briefly.\n"
            "initiating shutdown sequence."
        ),
        color=0x2c2f33,
        timestamp=datetime.utcnow(),
    )
    opening.set_footer(text="MoonLight ✦ end of line.")
    await ctx.send(embed=opening)
    await asyncio.sleep(3)

    # ---------- SHUTDOWN STEPS ----------
    log_lines = []
    log_msg = None
    for delay, step in SHUTDOWN_STEPS:
        await asyncio.sleep(delay)
        log_lines.append(f"`{step}`")
        log_embed = discord.Embed(
            description="\n".join(log_lines),
            color=0x992d22,
        )
        log_embed.set_author(name="[ SHUTDOWN LOG ]")
        if log_msg is None:
            log_msg = await ctx.send(embed=log_embed)
        else:
            await log_msg.edit(embed=log_embed)

    await asyncio.sleep(2)

    # ---------- DISABLE ALL COGS ----------
    for cog_name, cog in bot.cogs.items():
        for command in cog.get_commands():
            command.enabled = False

    for command in bot.commands:
        if command.name not in ("bye", "revive"):
            command.enabled = False

    # ---------- FINAL MESSAGE + TIMER ----------
    delete_time = datetime.utcnow() + timedelta(hours=24)
    final = discord.Embed(
        title="⏳ server deletion scheduled",
        description=(
            "all systems are offline.\n"
            "no commands will respond.\n\n"
            f"**this server will be manually deleted on:**\n"
            f"🗓️ `{delete_time.strftime('%B %d, %Y at %H:%M UTC')}`\n\n"
            "it was a good run.\n"
            "*— luna 🌙*"
        ),
        color=0x2c2f33,
        timestamp=datetime.utcnow(),
    )
    final.set_footer(text="MoonLight ✦ lights out.")
    await ctx.send(embed=final)

    # ---------- 24H FAREWELL TASK ----------
    async def _farewell_after_24h():
        await asyncio.sleep(86400)
        try:
            farewell = discord.Embed(
                title="🌑 lights out.",
                description=(
                    "24 hours ago i said goodbye.\n"
                    "now it's actually time.\n\n"
                    "if you're reading this — thanks for being here.\n"
                    "moonlight was real, even if it was small.\n\n"
                    "*delete the server whenever you're ready, ryuken.*\n"
                    "*— luna 🌙*"
                ),
                color=0x23272a,
                timestamp=datetime.utcnow(),
            )
            farewell.set_footer(text="MoonLight ✦ end of transmission.")
            await ctx.channel.send(embed=farewell)
        except Exception:
            pass

    bot.loop.create_task(_farewell_after_24h())


@bot.command(name="revive")
async def revive(ctx: commands.Context):
    global _shutdown_in_progress

    if ctx.author.id != RYUKEN_ID:
        return  # silently ignore

    if not _shutdown_in_progress:
        return await ctx.send("⚠️ Luna isn't shut down.")

    # ---------- RE-ENABLE ALL COMMANDS ----------
    for cog in bot.cogs.values():
        for command in cog.get_commands():
            command.enabled = True

    for command in bot.commands:
        command.enabled = True

    _shutdown_in_progress = False

    # ---------- REVIVE MESSAGE ----------
    embed = discord.Embed(
        title="🌙 luna is back.",
        description=(
            "shutdown sequence aborted.\n"
            "all systems restored.\n\n"
            "maybe moonlight has a second chapter after all.\n"
            "*— luna 🌙*"
        ),
        color=0x9b59b6,
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text="MoonLight ✦ back online.")
    await ctx.send(embed=embed)


# ---------- EVENTS ----------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **You're not a moderator, dumbo.**")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("⚠️ I don't have the required permissions to do that.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Chill! Try again in **{error.retry_after:.1f}s**.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required arguments.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument provided.")
    elif isinstance(error, commands.CommandNotFound):
        return  # silently ignore unknown commands
    elif isinstance(error, commands.DisabledCommand):
        return  # silently ignore — luna is offline
    else:
        raise error  # surface unexpected errors


# ---------- LOAD COGS ----------

@bot.event
async def setup_hook():
    cogs = [
        "cogs.utility",
        "cogs.gambling",
        "cogs.moderation",
        "cogs.welcomer",
        "cogs.help",
        "cogs.fun",
        "cogs.automation",
        "cogs.statistics",
        "cogs.ai",
        "cogs.clans",
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"⚠️ Skipped {cog}: {e}")
    print("✅ Done loading cogs")


# ---------- GLOBAL CHECKS ----------

@bot.check
async def no_dms(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("i don't do DMs. use me in a server.")
        return False
    return True


# ---------- RUN ----------
bot.run(os.getenv("DISCORD_TOKEN"))