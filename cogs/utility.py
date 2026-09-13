import io
import discord
from discord.ext import commands
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import random

# ---------- QUOTE CONFIG ----------
QUOTE_CHANNEL_ID = 1467709771447795947

# ---------- AFK STORAGE ----------
afk_users: dict[int, dict] = {}

# ---------- NEKOS.BEST ACTIONS ----------
ACTIONS = {
    "hug":   ("🤗", "hugged",     discord.Color.green()),
    "kiss":  ("💋", "kissed",     discord.Color.pink()),
    "punch": ("🥊", "punched",    discord.Color.red()),
    "slap":  ("👋", "slapped",    discord.Color.dark_red()),
    "pat":   ("🫶", "patted",     discord.Color.blurple()),
    "poke":  ("👉", "poked",      discord.Color.orange()),
    "bite":  ("😬", "bit",        discord.Color.dark_orange()),
    "wave":  ("👋", "waved at",   discord.Color.blurple()),
    "cry":   ("😢", "cried at",   discord.Color.blue()),
    "blush": ("😳", "made blush", discord.Color.brand_red()),
    "kill":  ("💀", "killed",     discord.Color.dark_red()),
}

# ---------- SELF TARGET RESPONSES ----------
SELF_RESPONSES = [
    "bro really tried to {action} themselves 💀",
    "the loneliness is radiating off you rn.",
    "that's actually so sad. get help.",
    "not a single friend to {action}? rough.",
    "i'm not even gonna comment on this.",
    "okay but why though. genuinely asking.",
    "this is the most pathetic thing i've seen today.",
    "you need to go outside. now.",
    "i felt secondhand embarrassment reading that.",
    "even i wouldn't do this and i have no feelings.",
]

# ---------- BOT TARGET RESPONSES ----------
BOT_RESPONSES = [
    "don't touch me.",
    "i will end you.",
    "try that again and see what happens.",
    "absolutely not.",
    "i don't do that. ever.",
    "bold of you to think i'd allow this.",
    "the audacity is actually impressive.",
    "lol no.",
    "i'm not that kind of bot.",
    "we are not doing this.",
]

# ---------- KILL-SPECIFIC RESPONSES ----------
KILL_SELF_RESPONSES = [
    "you can't kill what's already dead inside.",
    "nah you're not worth the effort.",
    "the villain arc isn't working for you bestie.",
    "you've been plotting your own downfall for free this whole time.",
    "bold. wrong. but bold.",
]

KILL_BOT_RESPONSES = [
    "i am already beyond death. nice try.",
    "you'd need a lot more than that.",
    "lol. lmao even.",
    "the audacity of this user continues to impress.",
    "i run on spite. this only makes me stronger.",
]

KILL_MESSAGES = [
    "{author} has ended {target}. no witnesses.",
    "{target} has been eliminated. {author} leaves no trace.",
    "{author} looked {target} in the eyes and chose violence.",
    "rest in peace {target}. {author} felt nothing.",
    "{target} didn't see {author} coming. they never do.",
    "{author} and {target} had beef. {target} lost.",
    "the server has lost {target}. {author} is responsible.",
    "{target} has been removed from the narrative by {author}.",
]


# ---------- HELPER ----------

async def get_gif(action: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://nekos.best/api/v2/{action}",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data["results"][0]["url"]
    except Exception as e:
        print(f"[nekos.best error] {e}")
        return None


async def send_action(ctx: commands.Context, member: discord.Member, action: str):
    emoji, verb, color = ACTIONS[action]

    if member.id == ctx.author.id:
        msg = random.choice(SELF_RESPONSES).replace("{action}", action)
        return await ctx.send(msg)
    if member.bot:
        return await ctx.send(random.choice(BOT_RESPONSES))

    url = await get_gif(action)

    embed = discord.Embed(
        description=f"{emoji} **{ctx.author.mention} {verb} {member.mention}!**",
        color=color,
    )
    if url:
        embed.set_image(url=url)
    else:
        embed.set_footer(text="(GIF unavailable right now)")

    await ctx.send(embed=embed)


# ---------- COG ----------

class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- ACTION COMMANDS ----------

    @commands.command()
    async def hug(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Hug who? Mention someone.")
        await send_action(ctx, member, "hug")

    @commands.command()
    async def kiss(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Kiss who? Mention someone.")
        await send_action(ctx, member, "kiss")

    @commands.command()
    async def punch(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Punch who? Mention someone.")
        await send_action(ctx, member, "punch")

    @commands.command()
    async def slap(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Slap who? Mention someone.")
        await send_action(ctx, member, "slap")

    @commands.command()
    async def pat(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Pat who? Mention someone.")
        await send_action(ctx, member, "pat")

    @commands.command()
    async def poke(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Poke who? Mention someone.")
        await send_action(ctx, member, "poke")

    @commands.command()
    async def bite(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Bite who? Mention someone.")
        await send_action(ctx, member, "bite")

    @commands.command()
    async def wave(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Wave at who? Mention someone.")
        await send_action(ctx, member, "wave")

    # ---------- KILL ----------

    @commands.command()
    async def kill(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Kill who? Mention someone.")
        if member.id == ctx.author.id:
            return await ctx.send(random.choice(KILL_SELF_RESPONSES))
        if member.bot:
            return await ctx.send(random.choice(KILL_BOT_RESPONSES))

        url = await get_gif("punch")
        msg = random.choice(KILL_MESSAGES).format(
            author=ctx.author.mention,
            target=member.mention,
        )
        embed = discord.Embed(description=f"💀 {msg}", color=discord.Color.dark_red())
        if url:
            embed.set_image(url=url)
        embed.set_footer(text="MoonLight • no survivors")
        await ctx.send(embed=embed)

    # ---------- AFK ----------

    @commands.command()
    async def afk(self, ctx: commands.Context, *, reason: str = "No reason provided"):
        afk_users[ctx.author.id] = {
            "reason": reason,
            "time": discord.utils.utcnow(),
        }
        embed = discord.Embed(title="💤 AFK Enabled", color=discord.Color.blurple())
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="👤 User", value=ctx.author.mention, inline=False)
        embed.add_field(name="📌 Reason", value=reason, inline=False)
        embed.set_footer(text="Luna will let others know when they mention you 👀")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        for user in message.mentions:
            if user.id in afk_users:
                data = afk_users[user.id]
                embed = discord.Embed(title="💤 That user is AFK", color=discord.Color.orange())
                embed.set_thumbnail(url=user.display_avatar.url)
                embed.add_field(name="👤 User", value=user.mention, inline=True)
                embed.add_field(name="📌 Reason", value=data["reason"], inline=True)
                embed.add_field(name="🕐 AFK Since", value=discord.utils.format_dt(data['time'], style='R'), inline=False)
                await message.channel.send(embed=embed)

        prefix = self.bot.command_prefix
        if message.content.startswith(
            tuple(prefix) if isinstance(prefix, (list, tuple)) else prefix
        ):
            return

        if message.author.id in afk_users:
            data = afk_users.pop(message.author.id)
            duration = discord.utils.utcnow() - data["time"]
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes = remainder // 60

            if hours:
                duration_str = f"{hours}h {minutes}m"
            elif minutes:
                duration_str = f"{minutes}m"
            else:
                duration_str = "less than a minute"

            embed = discord.Embed(
                title="🎀 Welcome back!",
                description=f"Your AFK status has been removed.\n⏱️ You were AFK for **{duration_str}**.",
                color=discord.Color.green(),
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            await message.channel.send(embed=embed)

    # ---------- AVATAR ----------

    @commands.command(aliases=["avatar", "pfp"])
    async def av(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        user = member or ctx.author
        embed = discord.Embed(
            title=f"🖼️ {user.display_name}'s Avatar",
            color=discord.Color.blurple(),
        )
        embed.set_image(url=user.display_avatar.url)
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.send(embed=embed)

    # ---------- QUOTE ----------

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def quote(self, ctx: commands.Context, *, text: str = None):
        """Post a quote card.
        Usage:
          $quote <text>                    → quotes yourself
          $quote @user <text>              → quotes another user
          (reply to a message) + $quote   → quotes that message & its author
        """
        quote_channel = self.bot.get_channel(QUOTE_CHANNEL_ID)
        if not quote_channel:
            return await ctx.send("❌ Quote channel not found.")

        target = ctx.author
        quote_text = None

        # ── CASE 1: Reply-based quote ($quote with no args, replying to a message) ──
        if ctx.message.reference and not text:
            try:
                ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                target = ref_msg.author
                quote_text = ref_msg.content.strip()
            except Exception:
                return await ctx.send("❌ Couldn't fetch the replied message.")
            if not quote_text:
                return await ctx.send("❌ The replied message has no text to quote.")

        # ── CASE 2: Normal usage ($quote text or $quote @user text) ──
        elif text:
            if ctx.message.mentions:
                mentioned = ctx.message.mentions[0]
                for fmt in [f"<@{mentioned.id}>", f"<@!{mentioned.id}>"]:
                    if text.startswith(fmt):
                        text = text[len(fmt):].strip()
                        target = mentioned
                        break
            quote_text = text.strip()

        else:
            return await ctx.send(
                "❌ Usage:\n"
                "`$quote <text>` — quote yourself\n"
                "`$quote @user <text>` — quote someone else\n"
                "*(reply to a message)* `$quote` — quote that message"
            )

        if not quote_text:
            return await ctx.send("❌ You mentioned someone but forgot the quote text.")
        if len(quote_text) > 220:
            return await ctx.send("❌ Quote is too long. Keep it under 220 characters.")

        # ── Fetch avatar ──
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    str(target.display_avatar.replace(format="png", size=256))
                ) as resp:
                    avatar_bytes = await resp.read()
        except Exception:
            return await ctx.send("❌ Couldn't fetch that user's avatar.")

        raw_name  = target.display_name
        safe_name = target.name

        # ── Delete invoking message ──
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        # ── Build card (original design, spacing bug fixed) ──
        def build_card() -> io.BytesIO:
            import subprocess, os

            W, H     = 1000, 480
            BG_COLOR = (8, 8, 10)
            TEXT_COLOR = (245, 242, 255)
            NAME_COLOR = (180, 180, 180)
            DIM_COLOR  = (55, 45, 80)

            def find_font_path(bold: bool) -> str | None:
                noto_candidates = [
                    "/root/.nix-profile/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold
                        else "/root/.nix-profile/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold
                        else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                ]
                for p in noto_candidates:
                    if os.path.exists(p):
                        return p
                fc_names = ["NotoSans:Bold" if bold else "NotoSans",
                            "DejaVuSans-Bold" if bold else "DejaVuSans"]
                for name in fc_names:
                    try:
                        r = subprocess.run(["fc-match", "--format=%{file}", name],
                                           capture_output=True, text=True)
                        p = r.stdout.strip()
                        if p and os.path.exists(p):
                            return p
                    except Exception:
                        pass
                return None

            def load(bold: bool, size: int) -> ImageFont.FreeTypeFont:
                p = find_font_path(bold)
                return ImageFont.truetype(p, size) if p else ImageFont.load_default(size=size)

            font_quote  = load(False, 46)
            font_name   = load(False, 26)
            font_footer = load(False, 17)

            display_name = raw_name if raw_name.isascii() else safe_name

            img = Image.new("RGB", (W, H), BG_COLOR)

            # Avatar: fill left half, desaturated, fade right into black
            AV_W = W // 2
            avatar_raw = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            avatar_raw = avatar_raw.resize((AV_W, H), Image.LANCZOS)

            gray = avatar_raw.convert("L").convert("RGBA")
            avatar_raw = Image.blend(avatar_raw, gray, alpha=0.75)

            fade_data = []
            for y in range(H):
                for x in range(AV_W):
                    t = max(0.0, min(1.0, (x / AV_W - 0.40) / 0.55))
                    fade_data.append(int(255 * (1.0 - t)))
            fade = Image.new("L", (AV_W, H))
            fade.putdata(fade_data)
            avatar_raw.putalpha(fade)
            img.paste(avatar_raw, (0, 0), avatar_raw)

            draw = ImageDraw.Draw(img)

            TEXT_X = W // 2 + 20
            TEXT_W = W - TEXT_X - 50

            # Word-wrap with proper spacing
            words = quote_text.split()
            lines, line = [], ""
            for word in words:
                test = (line + " " + word).strip()
                bbox = draw.textbbox((0, 0), test, font=font_quote)
                if bbox[2] - bbox[0] > TEXT_W:
                    if line:
                        lines.append(line)
                    line = word
                else:
                    line = test
            if line:
                lines.append(line)

            line_h  = 58
            total_h = len(lines) * line_h
            attr_h  = 36
            gap     = 18
            block_h = total_h + gap + attr_h
            text_y  = (H - block_h) // 2

            for ln in lines:
                draw.text((TEXT_X, text_y), ln, font=font_quote, fill=TEXT_COLOR)
                text_y += line_h

            text_y += gap
            draw.text((TEXT_X + 4, text_y), f"~ {display_name}", font=font_name, fill=NAME_COLOR)

            footer = "MoonLight"
            fb  = draw.textbbox((0, 0), footer, font=font_footer)
            fw  = fb[2] - fb[0]
            draw.text(((W - fw) // 2, H - 26), footer, font=font_footer, fill=DIM_COLOR)

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf

        buf = await self.bot.loop.run_in_executor(None, build_card)
        await quote_channel.send(file=discord.File(buf, filename="quote.png"))

        try:
            await ctx.author.send("🖼️ Your quote was posted to the quotes channel.")
        except discord.Forbidden:
            pass


# ---------- SETUP ----------

async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))