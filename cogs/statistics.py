import discord
from discord.ext import commands, tasks
from datetime import datetime
import time
import random

from moonlight.database import (
    add_message,
    add_voice_time,
    get_user_activity,
    get_message_leaderboard,
    get_voice_leaderboard,
    reset_message_counts,
    get_last_reset,
)

RESET_INTERVAL_HOURS = 24


# ---------- HELPERS ----------

def _fmt_voice(seconds: int) -> str:
    """Convert seconds into a readable duration string."""
    if seconds < 60:
        return f"{seconds}s"
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _activity_bar(value: int, max_value: int, length: int = 10) -> str:
    """Generate a visual progress bar."""
    if max_value == 0:
        filled = 0
    else:
        filled = min(length, round((value / max_value) * length))
    return "🟣" * filled + "⬛" * (length - filled)


def _rank_label(messages: int, voice: int) -> tuple[str, str]:
    score = messages + (voice // 60)
    if score >= 10000:
        return "🌙 Moonlight Legend", "You ARE the server. Bow down, everyone."
    elif score >= 5000:
        return "💎 Crystal Member", "Deeply embedded in this place."
    elif score >= 2000:
        return "⭐ Star Member", "A familiar face around here."
    elif score >= 500:
        return "🔥 Active Member", "You're showing up consistently."
    elif score >= 100:
        return "🌱 Rising Member", "You're finding your footing."
    else:
        return "👤 New Member", "Just getting started. Go touch some channels."


def _next_rank_info(messages: int, voice: int) -> tuple[str, int] | None:
    score = messages + (voice // 60)
    thresholds = [
        (100,  "🌱 Rising Member"),
        (500,  "🔥 Active Member"),
        (2000, "⭐ Star Member"),
        (5000, "💎 Crystal Member"),
        (10000,"🌙 Moonlight Legend"),
    ]
    for threshold, name in thresholds:
        if score < threshold:
            return name, threshold - score
    return None


def _random_tip() -> str:
    tips = [
        "💡 Tip: Chatting in voice channels still counts toward your score!",
        "💡 Tip: The more you talk, the higher you climb.",
        "💡 Tip: Legends are made one message at a time.",
        "💡 Tip: Consistency beats intensity. Keep showing up.",
        "💡 Tip: You miss 100% of the voice chats you don't join.",
        "💡 Tip: Every message is a step closer to the top.",
    ]
    return random.choice(tips)


def _streak_flavor(messages: int) -> str:
    if messages >= 10000:
        return "🗣️ You've sent **10,000+** messages. Do you ever log off?"
    elif messages >= 5000:
        return "🗣️ **5,000+** messages sent. You basically live here."
    elif messages >= 1000:
        return "🗣️ **1,000+** messages. A true server regular."
    elif messages >= 500:
        return "🗣️ **500+** messages. You're warming up nicely."
    elif messages >= 100:
        return "🗣️ **100+** messages. You found your voice."
    else:
        return "🗣️ Still getting started — say hi sometime!"


def _voice_flavor(voice: int) -> str:
    hours = voice // 3600
    if hours >= 100:
        return "🎙️ **100+ hours** in VC. You might just live here."
    elif hours >= 50:
        return "🎙️ **50+ hours** in VC. Certified voice chat goblin."
    elif hours >= 10:
        return "🎙️ **10+ hours** in VC. You clearly enjoy the company."
    elif hours >= 1:
        return f"🎙️ **{hours}h** in VC. A solid start."
    else:
        return "🎙️ Barely any voice time. Your mic misses you."


def _fmt_timestamp(ts: int) -> str:
    """Format a Unix timestamp into a readable string."""
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")


# ---------- COG ----------

class Statistics(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_sessions: dict[int, float] = {}
        self._reset_channel_id: int | None = None  # set via $setresetchannel
        self.leaderboard_reset_task.start()

    def cog_unload(self):
        self.leaderboard_reset_task.cancel()

    # ---------- 24H RESET TASK ----------

    @tasks.loop(hours=RESET_INTERVAL_HOURS)
    async def leaderboard_reset_task(self):
        """Wipes message counts every 24 hours and announces it."""
        # Skip the very first fire on startup (bot just booted)
        if not self.bot.is_ready():
            return

        reset_message_counts()

        if self._reset_channel_id:
            channel = self.bot.get_channel(self._reset_channel_id)
            if channel:
                embed = discord.Embed(
                    title="🔄 Leaderboard Reset!",
                    description=(
                        "The **message leaderboard** has been wiped.\n"
                        "Everyone starts fresh — go get that top spot! 🏆"
                    ),
                    color=0x9B59B6,
                    timestamp=datetime.utcnow(),
                )
                embed.set_footer(text="MoonLight • Auto-reset every 24h 🌙")
                await channel.send(embed=embed)

    @leaderboard_reset_task.before_loop
    async def before_reset_task(self):
        """Wait until the bot is fully ready, then align the first fire
        to exactly 24h after the last recorded reset."""
        await self.bot.wait_until_ready()

        last = get_last_reset()
        elapsed = time.time() - last
        remaining = max(0.0, RESET_INTERVAL_HOURS * 3600 - elapsed)

        if remaining > 0:
            await discord.utils.sleep_until(
                datetime.utcfromtimestamp(time.time() + remaining)
            )

    # ---------- SET RESET CHANNEL ----------

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setresetchannel(self, ctx: commands.Context):
        """Set this channel as the one that receives leaderboard reset announcements."""
        self._reset_channel_id = ctx.channel.id
        await ctx.send(
            f"✅ Reset announcements will be posted here every **{RESET_INTERVAL_HOURS}h**."
        )

    # ---------- RESET STATUS ----------

    @commands.command(aliases=["resetinfo"])
    async def resetstatus(self, ctx: commands.Context):
        """Check when the leaderboard last reset and when the next one is."""
        last = get_last_reset()
        next_reset_ts = last + RESET_INTERVAL_HOURS * 3600
        now = int(time.time())
        remaining_secs = max(0, next_reset_ts - now)

        hours, r = divmod(remaining_secs, 3600)
        minutes = r // 60

        embed = discord.Embed(
            title="🔄 Leaderboard Reset Status",
            color=0x3498DB,
            timestamp=datetime.utcnow(),
        )
        embed.add_field(
            name="🕒 Last Reset",
            value=_fmt_timestamp(last),
            inline=False,
        )
        embed.add_field(
            name="⏳ Next Reset In",
            value=f"**{hours}h {minutes}m**",
            inline=False,
        )
        embed.set_footer(text="MoonLight • Resets every 24h 🌙")
        await ctx.send(embed=embed)

    # ---------- MANUAL RESET (admin only) ----------

    @commands.command(aliases=["forcereset"])
    @commands.has_permissions(administrator=True)
    async def manualreset(self, ctx: commands.Context):
        """Manually wipe the message leaderboard right now (admin only)."""
        reset_message_counts()

        # Restart the loop timer so the next auto-reset is 24h from now
        self.leaderboard_reset_task.restart()

        embed = discord.Embed(
            title="🔄 Manual Reset Done",
            description="Message leaderboard wiped. Next auto-reset is in **24 hours**.",
            color=0xE74C3C,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"Reset triggered by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    # ---------- MESSAGE TRACKING ----------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        add_message(message.author.id)

    # ---------- VOICE TRACKING ----------

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return

        now = time.time()

        if before.channel is None and after.channel is not None:
            self.voice_sessions[member.id] = now

        elif before.channel is not None and after.channel is None:
            start = self.voice_sessions.pop(member.id, None)
            if start:
                duration = int(now - start)
                add_voice_time(member.id, duration)

        elif before.channel is not None and after.channel is not None:
            if before.channel != after.channel:
                start = self.voice_sessions.pop(member.id, None)
                if start:
                    duration = int(now - start)
                    add_voice_time(member.id, duration)
                self.voice_sessions[member.id] = now

    # ---------- ACTIVITY ----------

    @commands.command(aliases=["stats", "profile"])
    async def activity(self, ctx: commands.Context, member: discord.Member = None):
        """Show a user's full activity profile."""
        member = member or ctx.author
        messages, voice = get_user_activity(member.id)

        rank_title, rank_desc = _rank_label(messages, voice)

        top = get_message_leaderboard(50)
        user_rank = next((i + 1 for i, (uid, _) in enumerate(top) if uid == member.id), None)
        rank_str = f"**#{user_rank}** on the server" if user_rank else "Not ranked yet"

        next_info = _next_rank_info(messages, voice)
        if next_info:
            next_name, pts_needed = next_info
            next_rank_str = f"**{pts_needed:,}** points away from {next_name}"
        else:
            next_rank_str = "🏆 You've reached the highest rank!"

        # Show time until next reset
        last = get_last_reset()
        remaining_secs = max(0, last + RESET_INTERVAL_HOURS * 3600 - int(time.time()))
        hrs, rem = divmod(remaining_secs, 3600)
        reset_str = f"Leaderboard resets in **{hrs}h {rem // 60}m**"

        embed = discord.Embed(
            title=rank_title,
            description=f"*{rank_desc}*",
            color=member.color if member.color.value else discord.Color.blurple(),
            timestamp=datetime.utcnow(),
        )
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="💬 Messages",
            value=f"**{messages:,}**\n{_activity_bar(messages, 5000)}",
            inline=True,
        )
        embed.add_field(
            name="🎙️ Voice Time",
            value=f"**{_fmt_voice(voice)}**\n{_activity_bar(voice, 72000)}",
            inline=True,
        )
        embed.add_field(name="🏆 Leaderboard Rank", value=rank_str, inline=False)
        embed.add_field(name="📈 Next Rank", value=next_rank_str, inline=False)
        embed.add_field(name="\u200b", value=_streak_flavor(messages), inline=False)
        embed.add_field(name="\u200b", value=_voice_flavor(voice), inline=False)
        embed.set_footer(text=f"MoonLight • {reset_str}")
        await ctx.send(embed=embed)

    # ---------- MESSAGE LEADERBOARD ----------

    @commands.command(aliases=["msgstop", "topmessages"])
    async def messages(self, ctx: commands.Context):
        """Top 10 users by message count."""
        rows = get_message_leaderboard(10)

        if not rows:
            return await ctx.send("📊 No message data yet.")

        medals = ["🥇", "🥈", "🥉"]
        lines = []

        for i, (user_id, count) in enumerate(rows, start=1):
            medal = medals[i - 1] if i <= 3 else f"`#{i}`"
            user = self.bot.get_user(user_id)
            name = user.display_name if user else f"Unknown ({user_id})"
            highlight = " ◀ **you**" if user_id == ctx.author.id else ""
            lines.append(f"{medal} **{name}** — `{count:,}` messages{highlight}")

        # Time until next reset
        last = get_last_reset()
        remaining_secs = max(0, last + RESET_INTERVAL_HOURS * 3600 - int(time.time()))
        hrs, rem = divmod(remaining_secs, 3600)

        embed = discord.Embed(
            title="💬 Message Leaderboard",
            description="\n".join(lines),
            color=0x5865F2,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"MoonLight • Resets in {hrs}h {rem // 60}m 🔄")
        await ctx.send(embed=embed)

    # ---------- VOICE LEADERBOARD ----------

    @commands.command(aliases=["vctop", "topvoice"])
    async def voicetop(self, ctx: commands.Context):
        """Top 10 users by voice time."""
        rows = get_voice_leaderboard(10)

        if not rows:
            return await ctx.send("🎙️ No voice data yet. Someone get in VC!")

        medals = ["🥇", "🥈", "🥉"]
        lines = []

        for i, (user_id, seconds) in enumerate(rows, start=1):
            medal = medals[i - 1] if i <= 3 else f"`#{i}`"
            user = self.bot.get_user(user_id)
            name = user.display_name if user else f"Unknown ({user_id})"
            highlight = " ◀ **you**" if user_id == ctx.author.id else ""
            lines.append(f"{medal} **{name}** — `{_fmt_voice(seconds)}`{highlight}")

        embed = discord.Embed(
            title="🎙️ Voice Time Leaderboard",
            description="\n".join(lines),
            color=0x9B59B6,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text="MoonLight • Voice Stats 🎙️")
        await ctx.send(embed=embed)

    # ---------- COMPARE ----------

    @commands.command(aliases=["vs"])
    async def compare(self, ctx: commands.Context, member1: discord.Member, member2: discord.Member = None):
        """Compare activity stats between two users."""
        member2 = member2 or ctx.author
        m1_msgs, m1_voice = get_user_activity(member1.id)
        m2_msgs, m2_voice = get_user_activity(member2.id)

        m1_score = m1_msgs + (m1_voice // 60)
        m2_score = m2_msgs + (m2_voice // 60)

        winner = member1 if m1_score >= m2_score else member2
        diff = abs(m1_score - m2_score)

        embed = discord.Embed(
            title="⚔️ Activity Duel",
            description=f"**{member1.display_name}** vs **{member2.display_name}**",
            color=0xE91E63,
            timestamp=datetime.utcnow(),
        )
        embed.add_field(
            name=f"{member1.display_name}",
            value=(
                f"💬 `{m1_msgs:,}` messages\n"
                f"🎙️ `{_fmt_voice(m1_voice)}`\n"
                f"⚡ Score: `{m1_score:,}`"
            ),
            inline=True,
        )
        embed.add_field(name="VS", value="\u200b", inline=True)
        embed.add_field(
            name=f"{member2.display_name}",
            value=(
                f"💬 `{m2_msgs:,}` messages\n"
                f"🎙️ `{_fmt_voice(m2_voice)}`\n"
                f"⚡ Score: `{m2_score:,}`"
            ),
            inline=True,
        )
        embed.add_field(
            name="🏆 Winner",
            value=f"**{winner.display_name}** wins by `{diff:,}` points!" if diff > 0 else "It's a **tie**! 🤝",
            inline=False,
        )
        embed.set_footer(text="MoonLight • Activity Duel ⚔️")
        await ctx.send(embed=embed)

    # ---------- SERVER STATS ----------

    @commands.command(aliases=["serverstats", "ss"])
    async def globalstats(self, ctx: commands.Context):
        """Show overall server activity stats."""
        rows = get_message_leaderboard(999)
        total_messages = sum(count for _, count in rows)
        total_tracked = len(rows)

        voice_now = sum(
            1 for vc in ctx.guild.voice_channels
            for m in vc.members if not m.bot
        )

        most_active_str = "N/A"
        if rows:
            top_uid, top_count = rows[0]
            top_user = self.bot.get_user(top_uid)
            top_name = top_user.display_name if top_user else f"Unknown ({top_uid})"
            most_active_str = f"**{top_name}** with `{top_count:,}` messages"

        avg_msgs = total_messages // total_tracked if total_tracked else 0

        embed = discord.Embed(
            title=f"📊 {ctx.guild.name} — Server Stats",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow(),
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.add_field(name="👥 Members", value=f"**{ctx.guild.member_count:,}**", inline=True)
        embed.add_field(name="💬 Total Messages Tracked", value=f"**{total_messages:,}**", inline=True)
        embed.add_field(name="📋 Tracked Users", value=f"**{total_tracked:,}**", inline=True)
        embed.add_field(name="🎙️ In Voice Right Now", value=f"**{voice_now}**", inline=True)
        embed.add_field(name="📈 Avg Messages / User", value=f"**{avg_msgs:,}**", inline=True)
        embed.add_field(name="👑 Most Active", value=most_active_str, inline=False)
        embed.set_footer(text="MoonLight • Server Statistics 📊")
        await ctx.send(embed=embed)

    # ---------- FLEX ----------

    @commands.command(aliases=["brag"])
    async def flex(self, ctx: commands.Context):
        """Show off your stats with extra flair."""
        member = ctx.author
        messages, voice = get_user_activity(member.id)
        rank_title, _ = _rank_label(messages, voice)
        score = messages + (voice // 60)

        top = get_message_leaderboard(50)
        user_rank = next((i + 1 for i, (uid, _) in enumerate(top) if uid == member.id), None)

        flex_lines = [
            f"👤 **{member.display_name}** is out here **flexing**.",
            f"🏅 Rank: **{rank_title}**",
            f"💬 **{messages:,}** messages sent.",
            f"🎙️ **{_fmt_voice(voice)}** in voice channels.",
            f"⚡ Activity score: **{score:,}**",
        ]
        if user_rank:
            flex_lines.append(f"🏆 Top **#{user_rank}** on the server leaderboard.")

        flex_lines.append("\n*Skill issue if you can't match this.* 😤")

        embed = discord.Embed(
            description="\n".join(flex_lines),
            color=0xF1C40F,
            timestamp=datetime.utcnow(),
        )
        embed.set_author(name="💪 FLEX MODE ACTIVATED", icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="MoonLight • No cap 🚫🧢")
        await ctx.send(embed=embed)


# ---------- SETUP ----------

async def setup(bot: commands.Bot):
    await bot.add_cog(Statistics(bot))