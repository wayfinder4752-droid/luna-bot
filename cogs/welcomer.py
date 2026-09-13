import discord
from discord.ext import commands
from datetime import datetime, timezone

WELCOME_CHANNEL_ID = 1463136856374906887

# Account age threshold in days — flag accounts newer than this
NEW_ACCOUNT_THRESHOLD = 7


class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- JOIN ----------

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if channel is None:
            return

        # Account age check
        now = datetime.now(timezone.utc)
        account_age = (now - member.created_at).days
        is_new_account = account_age < NEW_ACCOUNT_THRESHOLD

        joined = (
            discord.utils.format_dt(member.joined_at, style="R")
            if member.joined_at else "Just now"
        )

        embed = discord.Embed(
            title="🎉 Welcome to the server!",
            description=(
                f"Hey {member.mention}, welcome to **{member.guild.name}**!\n\n"
                "Make sure to read the rules and enjoy your stay 🌙"
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url="https://media.tenor.com/vSHxRJFwAa8AAAAC/welcome-hello.gif")

        embed.add_field(name="👤 Member", value=member.mention, inline=True)
        embed.add_field(name="🪪 Account Created", value=discord.utils.format_dt(member.created_at, style="R"), inline=True)
        embed.add_field(name="📥 Joined", value=joined, inline=True)

        if is_new_account:
            embed.add_field(
                name="⚠️ New Account",
                value=f"This account is only **{account_age} day(s)** old.",
                inline=False,
            )

        embed.set_footer(text=f"Member #{member.guild.member_count} • MoonLight 🌙")

        await channel.send(embed=embed)

    # ---------- LEAVE ----------

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if channel is None:
            return

        # How long were they here?
        if member.joined_at:
            duration = datetime.now(timezone.utc) - member.joined_at
            days = duration.days
            if days >= 365:
                stay = f"{days // 365}y {(days % 365) // 30}m"
            elif days >= 30:
                stay = f"{days // 30} month(s)"
            elif days >= 1:
                stay = f"{days} day(s)"
            else:
                stay = "Less than a day"
        else:
            stay = "Unknown"

        embed = discord.Embed(
            title="👋 Someone left...",
            description=(
                f"**{member.display_name}** has left **{member.guild.name}**.\n\n"
                "*Luna noticed. Said nothing. As always.*"
            ),
            color=discord.Color.dark_gray(),
            timestamp=datetime.now(timezone.utc),
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 User", value=str(member), inline=True)
        embed.add_field(name="⏳ Time Here", value=stay, inline=True)
        embed.set_footer(text=f"Members remaining: {member.guild.member_count} • MoonLight 🌙")

        await channel.send(embed=embed)


# ---------- SETUP ----------

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))