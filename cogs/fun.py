import asyncio
import random
import discord
from discord.ext import commands
from datetime import datetime

# ---------- CONFIG ----------
OWNER_IDS = {1099923662267760745, 948613491999264838}  # Ryuken + Aizen
CONFESS_CHANNEL_ID = 1467709912908959744

# ---------- PERSISTENT MARRIAGE STORE ----------
# Keyed by user_id → partner_id
marriages: dict[int, int] = {}

# ---------- CONFESSION STORE ----------
# Maps confession_number → author_id (only owners can see this)
confessions: dict[int, int] = {}
confession_counter: int = 0


# ---------- CONTENT POOLS ----------

FORTUNES = [
    "🌙 The moon says: trust the process.",
    "🌑 Darkness first. Growth later.",
    "✨ A win is closer than you think.",
    "🌕 Tonight is powerful for you.",
    "☄️ Chaos brings opportunity.",
    "🌌 The stars are aligned — barely.",
    "💫 Something you lost is coming back.",
    "🔮 An unexpected conversation will change your week.",
    "🌒 Patience is the move right now.",
    "🌟 You're being watched. In a good way.",
]

MOON_FACTS = [
    "🌕 The Moon is drifting away from Earth by ~3.8 cm per year.",
    "🌑 There are moonquakes caused by Earth's gravitational pull.",
    "🌓 The Moon has no atmosphere — no wind, no weather.",
    "🌙 Moonlight is just reflected sunlight.",
    "☄️ Humans last walked on the Moon in 1972.",
    "🌕 The Moon's gravity is ~17% of Earth's.",
    "🌑 It takes ~27.3 days for the Moon to orbit Earth.",
    "🌌 The Moon was likely formed from debris after a Mars-sized object hit Earth.",
    "🌗 Only 59% of the Moon's surface has ever been visible from Earth.",
    "🔭 The dark side of the Moon gets sunlight — just never faces us.",
]

ROASTS = [
    "has main character energy… in the tutorial.",
    "is built different. Not better. Just different.",
    "survives purely on luck and vibes.",
    "thinks they're mysterious. They're just quiet.",
    "is lowkey powerful but has no idea.",
    "peaked during character creation.",
    "is the NPC the main character talks to once and forgets.",
    "has the confidence of someone with nothing to lose.",
    "exists in the background of every important moment.",
    "would lose a staring contest with a loading screen.",
]

COMPLIMENTS = [
    "radiates main character energy and earns it.",
    "is built for exactly this moment.",
    "carries the server on their back without complaining.",
    "has that rare thing: actual depth.",
    "is the reason people stay.",
    "hits different, in all the right ways.",
    "is probably someone's favorite person right now.",
    "makes this place better just by being here.",
]

COSMIC_READINGS = [
    "🪐 Your aura is chaotic neutral.",
    "🌌 The universe is watching you closely.",
    "☄️ You're overdue for a plot twist.",
    "🌑 Something big is brewing in your orbit.",
    "✨ Luck is loading… please wait.",
    "🌙 You're in a liminal phase. Stay still.",
    "💫 A door is about to open that you didn't knock on.",
    "🔭 You're being pulled toward something you haven't named yet.",
]

PROPHECIES = [
    "A late night will change everything.",
    "You'll win when you least expect it.",
    "Someone will surprise you soon.",
    "A decision is closer than it feels.",
    "Your patience will pay off spectacularly.",
    "You will say something that lands perfectly.",
    "The thing you almost gave up on is almost done.",
    "A stranger will become important.",
    "What you've been building is almost ready.",
    "The quiet you're in right now is the calm before your moment.",
]

COMFORT = [
    "🌙 You're doing better than you think.",
    "✨ Take a breath. You're safe here.",
    "🌓 One step at a time. That's still moving.",
    "🌌 Even slow progress is progress.",
    "💜 Luna's got your back.",
    "🌕 Rest is not quitting.",
    "☄️ Hard phases end. Yours will too.",
    "🌙 You don't have to have it all figured out tonight.",
    "💫 The version of you from a year ago would be proud.",
    "🌑 It's okay to be tired. You've been doing a lot.",
]

EIGHT_BALL = [
    "🎱 It is certain.",
    "🎱 Without a doubt.",
    "🎱 Yes, definitely.",
    "🎱 You may rely on it.",
    "🎱 Most likely.",
    "🎱 Outlook good.",
    "🎱 Signs point to yes.",
    "🎱 Ask again later.",
    "🎱 Reply hazy, try again.",
    "🎱 Cannot predict now.",
    "🎱 Don't count on it.",
    "🎱 My reply is no.",
    "🎱 Very doubtful.",
    "🎱 Outlook not so good.",
    "🎱 Luna says absolutely not.",
    "🎱 The moon is silent on this matter.",
]

HEART_IMAGES = [
    "https://media.tenor.com/zGm5acSjHCIAAAAC/heart-glow.gif",
    "https://media.tenor.com/7OZz6WmYkXgAAAAC/pixel-heart.gif",
    "https://media.tenor.com/V9q8rY3fZCkAAAAC/heart-aesthetic.gif",
]

WEDDING_IMAGES = [
    "https://media.tenor.com/9p6nKxF4BzEAAAAC/anime-romance.gif",
]


# ---------- HELPERS ----------

def _luck_message(percent: int) -> str:
    if percent >= 90:
        return "🌟 Cosmic luck. Something rare is near."
    elif percent >= 70:
        return "🍀 Insanely lucky today."
    elif percent >= 50:
        return "✨ Decent luck. Play smart."
    elif percent >= 30:
        return "🌑 Unstable energy. Tread carefully."
    else:
        return "☄️ The stars aren't with you. Lay low."


def _ship_verdict(percent: int) -> tuple[str, discord.Color]:
    if percent >= 90:
        return "💍 Soulmates detected.", discord.Color.gold()
    elif percent >= 70:
        return "💖 Strong connection.", discord.Color.pink()
    elif percent >= 50:
        return "💫 There's something there.", discord.Color.purple()
    elif percent >= 30:
        return "😬 It's… complicated.", discord.Color.orange()
    else:
        return "💀 This ship has sunk.", discord.Color.dark_gray()


# ---------- COG ----------

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- LUNA ----------

    @commands.command()
    async def luna(self, ctx: commands.Context):
        """Luna's origin story."""
        embed = discord.Embed(
            title="🌙 Luna",
            description=(
                "I wasn't born overnight.\n\n"
                "I was built line by line — through bugs, crashes, rage, "
                "and way too much caffeine.\n\n"
                "**I exist because someone refused to quit.**"
            ),
            color=discord.Color.purple(),
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="📜 Lines of Code", value="**16725+** lines", inline=True)
        embed.add_field(name="⏱️ Time Spent", value="~**2 months+**", inline=True)
        embed.add_field(name="⭐ Creator", value="**Ryuken**", inline=True)
        embed.add_field(
            name="🧠 Built With",
            value="Patience, frustration, curiosity, and obsession",
            inline=False,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="MoonLight • Made from chaos, polished with discipline")
        await ctx.send(embed=embed)

    # ---------- FORTUNE / COSMIC / PROPHECY / COMFORT ----------

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def fortune(self, ctx: commands.Context):
        """Luna gives you a fortune."""
        embed = discord.Embed(
            title="🔮 Your Fortune",
            description=random.choice(FORTUNES),
            color=discord.Color.purple(),
        )
        embed.set_footer(text="MoonLight • Read it twice 🌙")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cosmic(self, ctx: commands.Context):
        """Luna reads your cosmic energy."""
        embed = discord.Embed(
            title="🌌 Cosmic Reading",
            description=random.choice(COSMIC_READINGS),
            color=0x1a1a2e,
        )
        embed.set_footer(text="MoonLight • The universe doesn't lie 🌙")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def prophecy(self, ctx: commands.Context):
        """Luna delivers a prophecy."""
        embed = discord.Embed(
            title="🔮 Prophecy",
            description=f"*{random.choice(PROPHECIES)}*",
            color=discord.Color.dark_purple(),
        )
        embed.set_footer(text="MoonLight • It will happen 🌙")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def comfort(self, ctx: commands.Context):
        """Luna says something kind."""
        embed = discord.Embed(
            description=random.choice(COMFORT),
            color=discord.Color.purple(),
        )
        embed.set_footer(text="MoonLight • You're okay 💜")
        await ctx.send(embed=embed)

    # ---------- MOON FACT ----------

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def moonfact(self, ctx: commands.Context):
        """A random moon fact."""
        embed = discord.Embed(
            title="🌙 Moon Fact",
            description=random.choice(MOON_FACTS),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="MoonLight • Space is wild ✨")
        await ctx.send(embed=embed)

    # ---------- LUCK ----------

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def luck(self, ctx: commands.Context):
        """Check your luck today."""
        percent = random.randint(1, 100)
        msg = _luck_message(percent)

        bar_filled = round(percent / 10)
        bar = "🟣" * bar_filled + "⬛" * (10 - bar_filled)

        embed = discord.Embed(
            title="🍀 Luck Check",
            description=f"{msg}\n\n{bar}\n**`{percent}%`**",
            color=discord.Color.purple(),
        )
        embed.set_footer(text="MoonLight • Luck changes daily 🌙")
        await ctx.send(embed=embed)

    # ---------- 8BALL ----------

    @commands.command(name="8ball", aliases=["ask", "oracle"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def eightball(self, ctx: commands.Context, *, question: str = None):
        """Ask Luna's oracle a question."""
        if not question:
            return await ctx.send("❌ Ask me something first.")

        embed = discord.Embed(
            title="🎱 Oracle",
            color=discord.Color.dark_purple(),
        )
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="🔮 Answer", value=random.choice(EIGHT_BALL), inline=False)
        embed.set_footer(text="MoonLight • The oracle has spoken 🌙")
        await ctx.send(embed=embed)

    # ---------- ROAST / COMPLIMENT ----------

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def roast(self, ctx: commands.Context, member: discord.Member = None):
        """Roast someone."""
        if not member:
            return await ctx.send("❌ Roast who? Mention someone.")
        if member.id == ctx.author.id:
            return await ctx.send("💀 You really came here to roast yourself?")
        if member.bot:
            return await ctx.send("i roast people, not myself. nice try.")

        embed = discord.Embed(
            description=f"🔥 {member.mention} {random.choice(ROASTS)}",
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name} 🌙")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def compliment(self, ctx: commands.Context, member: discord.Member = None):
        """Give someone a genuine compliment."""
        member = member or ctx.author
        if member.bot:
            return await ctx.send("obviously. i'm literally perfect.")
        embed = discord.Embed(
            description=f"💜 {member.mention} {random.choice(COMPLIMENTS)}",
            color=discord.Color.purple(),
        )
        embed.set_footer(text="MoonLight • Be kind 🌙")
        await ctx.send(embed=embed)

    # ---------- RATE ----------

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def rate(self, ctx: commands.Context, *, thing: str = None):
        """Luna rates anything you give her."""
        if not thing:
            return await ctx.send("❌ Rate what exactly?")

        score = random.randint(0, 10)
        bar = "🟣" * score + "⬛" * (10 - score)

        if score == 10:
            verdict = "Perfection. Luna approves."
        elif score >= 7:
            verdict = "Pretty solid honestly."
        elif score >= 4:
            verdict = "Mid. Could be worse."
        elif score >= 1:
            verdict = "Yikes. Room for improvement."
        else:
            verdict = "Luna refuses to acknowledge this."

        embed = discord.Embed(
            title="⭐ Luna Rates It",
            color=discord.Color.purple(),
        )
        embed.add_field(name="📌 Thing", value=thing, inline=False)
        embed.add_field(name="📊 Score", value=f"{bar} **{score}/10**", inline=False)
        embed.add_field(name="🔮 Verdict", value=verdict, inline=False)
        embed.set_footer(text="MoonLight • Luna's opinion is final 🌙")
        await ctx.send(embed=embed)

    # ---------- SHIP ----------

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ship(self, ctx: commands.Context, user1: discord.Member = None, user2: discord.Member = None):
        """Ship two people together."""
        if not user1:
            return await ctx.send("❌ Ship who? Mention at least one user.")

        if not user2:
            user2 = ctx.author

        if user1.id == user2.id:
            return await ctx.send("💀 You can't ship someone with themselves.")

        percent = random.randint(1, 100)
        verdict, color = _ship_verdict(percent)

        bar_filled = round(percent / 10)
        bar = "❤️" * bar_filled + "🖤" * (10 - bar_filled)

        embed = discord.Embed(
            title="💞 Ship Calculator",
            description=f"{user1.mention} ❤️ {user2.mention}",
            color=color,
        )
        embed.add_field(name="💯 Compatibility", value=f"{bar}\n**{percent}%**", inline=False)
        embed.add_field(name="🔮 Verdict", value=verdict, inline=False)
        embed.set_image(url=random.choice(HEART_IMAGES))
        embed.set_footer(text="MoonLight • Love is risky 🌙")
        await ctx.send(embed=embed)

    # ---------- MARRY / DIVORCE / SPOUSE ----------

    @commands.command()
    async def marry(self, ctx: commands.Context, partner: discord.Member = None):
        """Propose to someone."""
        if not partner:
            return await ctx.send("💀 Marry who? Mention someone.")
        if partner.bot:
            return await ctx.send("🤖 You can't marry a bot. Even Luna.")
        if partner.id == ctx.author.id:
            return await ctx.send("💀 You can't marry yourself.")
        if ctx.author.id in marriages:
            return await ctx.send("💔 You're already married. Loyal first.")
        if partner.id in marriages:
            return await ctx.send("💔 They're already taken.")

        embed = discord.Embed(
            title="💍 Marriage Proposal",
            description=(
                f"{partner.mention}\n\n"
                f"💖 **{ctx.author.mention} wants to marry you!**\n\n"
                "React with ❤️ to accept or ❌ to decline.\n"
                "*You have 60 seconds.*"
            ),
            color=discord.Color.pink(),
        )
        embed.set_image(url=random.choice(WEDDING_IMAGES))
        embed.set_footer(text="MoonLight • Love is a commitment 🌙")

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("❤️")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return (
                user.id == partner.id
                and reaction.message.id == msg.id
                and str(reaction.emoji) in ["❤️", "❌"]
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("⌛ Proposal expired. Love waited too long.")

        if str(reaction.emoji) == "❤️":
            marriages[ctx.author.id] = partner.id
            marriages[partner.id] = ctx.author.id

            embed = discord.Embed(
                title="💍 Just Married!",
                description=(
                    f"🎊 {ctx.author.mention} and {partner.mention} are now married!\n\n"
                    "*Luna blesses this union. Barely.*"
                ),
                color=discord.Color.gold(),
            )
            embed.set_footer(text="MoonLight • Congrats 💖")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"💔 {partner.mention} said no. Pain.")

    @commands.command()
    async def divorce(self, ctx: commands.Context):
        """End your marriage."""
        partner_id = marriages.get(ctx.author.id)
        if not partner_id:
            return await ctx.send("💀 You're not even married.")

        partner = ctx.guild.get_member(partner_id)
        marriages.pop(ctx.author.id, None)
        marriages.pop(partner_id, None)

        embed = discord.Embed(
            title="💔 Divorce Finalized",
            description=(
                f"{ctx.author.mention} and "
                f"{partner.mention if partner else '*someone who left*'} "
                f"are no longer married.\n\n*Luna witnessed this. Said nothing.*"
            ),
            color=discord.Color.dark_gray(),
        )
        embed.set_footer(text="MoonLight • It happens 🌙")
        await ctx.send(embed=embed)

    @commands.command()
    async def spouse(self, ctx: commands.Context, member: discord.Member = None):
        """Check who someone is married to."""
        member = member or ctx.author
        partner_id = marriages.get(member.id)

        if not partner_id:
            return await ctx.send(f"💀 {member.mention} is not married.")

        partner = ctx.guild.get_member(partner_id)
        embed = discord.Embed(
            description=(
                f"💍 {member.mention} is married to "
                f"{partner.mention if partner else '*someone who left the server*'}."
            ),
            color=discord.Color.pink(),
        )
        embed.set_footer(text="MoonLight • Relationship goals 🌙")
        await ctx.send(embed=embed)

    # ---------- CONFESS ----------

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def confess(self, ctx: commands.Context, *, confession: str = None):
        """Confess something anonymously."""
        if not confession:
            return await ctx.send("❌ You have to actually say something.")

        # Delete the command message immediately to protect identity
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        global confession_counter
        confession_counter += 1
        number = confession_counter

        # Store the author ID — only retrievable by owners in code
        confessions[number] = ctx.author.id

        # The public confession embed — completely anonymous
        confession_channel = self.bot.get_channel(CONFESS_CHANNEL_ID)
        if not confession_channel:
            return

        public_embed = discord.Embed(
            title=f"🕯️ Anonymous Confession  ·  #{number}",
            description=f"*❝ {confession} ❞*",
            color=0x2b2d31,
            timestamp=datetime.utcnow(),
        )
        public_embed.set_footer(text="MoonLight Confessions • Identity protected 🌙")
        public_embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        await confession_channel.send(embed=public_embed)

        # Silently DM the owners with the hidden identity
        author = ctx.author
        owner_embed = discord.Embed(
            title=f"🔍 Confession #{number} — Identity Revealed",
            description=f"*❝ {confession} ❞*",
            color=0x5865f2,
            timestamp=datetime.utcnow(),
        )
        owner_embed.add_field(name="👤 Sent by", value=f"{author.mention} (`{author}` · `{author.id}`)", inline=False)
        owner_embed.set_thumbnail(url=author.display_avatar.url)
        owner_embed.set_footer(text="MoonLight • For your eyes only 🌙")

        for owner_id in OWNER_IDS:
            try:
                owner = await self.bot.fetch_user(owner_id)
                await owner.send(embed=owner_embed)
            except Exception:
                pass

        # Confirm quietly to the user via DM so no trace in chat
        try:
            confirm_embed = discord.Embed(
                description="🕯️ Your confession was sent anonymously. No one can trace it back to you.",
                color=0x2b2d31,
            )
            confirm_embed.set_footer(text="MoonLight Confessions 🌙")
            await ctx.author.send(embed=confirm_embed)
        except Exception:
            pass


# ---------- SETUP ----------

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))