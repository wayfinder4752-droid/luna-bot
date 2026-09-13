import asyncio
import discord
from discord.ext import commands
from datetime import timedelta, datetime
from collections import defaultdict

# ---------- ROLE IDS ----------
MOD_ROLE_ID = 1463136855414280214
TRIAL_MOD_ROLE_ID = 1463136855347302512

# Tiers
MOD_ROLES = {MOD_ROLE_ID}
TRIAL_MOD_ROLES = {TRIAL_MOD_ROLE_ID}
ALL_MOD_ROLES = MOD_ROLES | TRIAL_MOD_ROLES

# Owners bypass all role checks
OWNER_IDS = {1099923662267760745, 948613491999264838}  # Ryuken + Aizen


# ---------- PERMISSION CHECKS ----------

def has_any_mod_role():
    async def predicate(ctx: commands.Context):
        if ctx.author.id in OWNER_IDS:
            return True
        user_role_ids = {r.id for r in ctx.author.roles}
        if user_role_ids & ALL_MOD_ROLES:
            return True
        raise commands.CheckFailure("❌ You don't have the required role to use this command.")
    return commands.check(predicate)


def has_mod_role():
    async def predicate(ctx: commands.Context):
        if ctx.author.id in OWNER_IDS:
            return True
        user_role_ids = {r.id for r in ctx.author.roles}
        if user_role_ids & MOD_ROLES:
            return True
        raise commands.CheckFailure("❌ This command requires the **Mod** role or higher.")
    return commands.check(predicate)


# ---------- IN-MEMORY STORES ----------
sniped_messages: dict[int, dict] = {}
edited_messages: dict[int, dict] = {}
warnings: dict[int, list[dict]] = defaultdict(list)


# ---------- HELPERS ----------

def _mod_embed(title: str, color: discord.Color, fields: list[tuple]) -> discord.Embed:
    embed = discord.Embed(title=title, color=color, timestamp=datetime.utcnow())
    for name, value in fields:
        embed.add_field(name=name, value=value, inline=False)
    embed.set_footer(text="MoonLight Moderation 🛡️")
    return embed


# ---------- COG ----------

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- ERROR HANDLER ----------

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))

    # ---------- KICK (Mod only) ----------

    @commands.command()
    @has_mod_role()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        await ctx.send(embed=_mod_embed(
            "👢 Member Kicked",
            discord.Color.orange(),
            [("👤 Member", member.mention), ("📝 Reason", reason), ("🔧 Moderator", ctx.author.mention)]
        ))

    # ---------- BAN (Mod only) ----------

    @commands.command()
    @has_mod_role()
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        await ctx.send(embed=_mod_embed(
            "🔨 Member Banned",
            discord.Color.red(),
            [("👤 Member", str(member)), ("📝 Reason", reason), ("🔧 Moderator", ctx.author.mention)]
        ))

    # ---------- UNBAN (Mod only) ----------

    @commands.command()
    @has_mod_role()
    async def unban(self, ctx: commands.Context, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(embed=_mod_embed(
                "✅ Member Unbanned",
                discord.Color.green(),
                [("👤 User", str(user)), ("🔧 Moderator", ctx.author.mention)]
            ))
        except discord.NotFound:
            await ctx.send("❌ User not found or not banned.")

    # ---------- SOFTBAN (Mod only) ----------

    @commands.command()
    @has_mod_role()
    async def softban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        await member.ban(reason=f"Softban: {reason}", delete_message_days=1)
        await ctx.guild.unban(member, reason="Softban unban")
        await ctx.send(embed=_mod_embed(
            "🧹 Member Softbanned",
            discord.Color.orange(),
            [("👤 Member", member.mention), ("📝 Reason", reason), ("🔧 Moderator", ctx.author.mention)]
        ))

    # ---------- TIMEOUT (Trial Mod+) ----------

    @commands.command(aliases=["mute"])
    @has_any_mod_role()
    async def timeout(self, ctx: commands.Context, member: discord.Member, minutes: int, *, reason: str = "No reason provided"):
        if minutes <= 0:
            return await ctx.send("❌ Duration must be greater than 0 minutes.")
        if minutes > 40320:
            return await ctx.send("❌ Max timeout is **28 days** (40,320 minutes).")

        until = discord.utils.utcnow() + timedelta(minutes=minutes)
        await member.timeout(until, reason=reason)

        h, m = divmod(minutes, 60)
        duration_str = f"{h}h {m}m" if h else f"{m}m"

        await ctx.send(embed=_mod_embed(
            "⏳ Member Timed Out",
            discord.Color.yellow(),
            [
                ("👤 Member", member.mention),
                ("⏱️ Duration", duration_str),
                ("📝 Reason", reason),
                ("🔧 Moderator", ctx.author.mention),
            ]
        ))

    # ---------- UNTIMEOUT (Trial Mod+) ----------

    @commands.command(aliases=["unmute", "untimeout"])
    @has_any_mod_role()
    async def removetimeout(self, ctx: commands.Context, member: discord.Member):
        await member.timeout(None)
        await ctx.send(embed=_mod_embed(
            "✅ Timeout Removed",
            discord.Color.green(),
            [("👤 Member", member.mention), ("🔧 Moderator", ctx.author.mention)]
        ))

    # ---------- WARN (Trial Mod+) ----------

    @commands.command()
    @has_any_mod_role()
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        entry = {
            "reason": reason,
            "moderator": str(ctx.author),
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
        warnings[member.id].append(entry)
        count = len(warnings[member.id])

        await ctx.send(embed=_mod_embed(
            f"⚠️ Warning Issued (#{count})",
            discord.Color.yellow(),
            [
                ("👤 Member", member.mention),
                ("📝 Reason", reason),
                ("🔢 Total Warnings", str(count)),
                ("🔧 Moderator", ctx.author.mention),
            ]
        ))

    # ---------- WARNINGS (Trial Mod+) ----------

    @commands.command(aliases=["warns", "infractions"])
    @has_any_mod_role()
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        user_warns = warnings.get(member.id, [])

        if not user_warns:
            return await ctx.send(f"✅ {member.mention} has no warnings.")

        embed = discord.Embed(
            title=f"⚠️ Warnings — {member.display_name}",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow(),
        )
        for i, w in enumerate(user_warns, 1):
            embed.add_field(
                name=f"#{i} — {w['time']}",
                value=f"📝 {w['reason']}\n🔧 By: {w['moderator']}",
                inline=False,
            )
        embed.set_footer(text="MoonLight Moderation 🛡️")
        await ctx.send(embed=embed)

    # ---------- CLEAR WARNINGS (Trial Mod+) ----------

    @commands.command(aliases=["clearwarns"])
    @has_any_mod_role()
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member):
        count = len(warnings.pop(member.id, []))
        await ctx.send(embed=_mod_embed(
            "🧹 Warnings Cleared",
            discord.Color.green(),
            [("👤 Member", member.mention), ("🗑️ Removed", f"{count} warning(s)"), ("🔧 Moderator", ctx.author.mention)]
        ))

    # ---------- CLEAR / PURGE (Trial Mod+) ----------

    @commands.command(name="clear", aliases=["purge"])
    @has_any_mod_role()
    async def clear(self, ctx: commands.Context, *, arg: str):
        MAX_SCAN = 100
        MAX_DELETE = 50

        await ctx.message.delete()
        arg_lower = arg.lower().strip()

        if arg_lower in ("bots", "contains bots"):
            deleted = []
            async for msg in ctx.channel.history(limit=MAX_SCAN):
                if msg.author.bot:
                    deleted.append(msg)
                    if len(deleted) >= MAX_DELETE:
                        break
            if not deleted:
                return await ctx.send("🤖 No recent bot messages found.", delete_after=3)
            await ctx.channel.delete_messages(deleted)
            return await ctx.send(f"🤖 Deleted **{len(deleted)}** bot messages.", delete_after=3)

        if arg_lower.startswith("user "):
            raw = arg[5:].strip()
            member_id = None
            if ctx.message.mentions:
                member_id = ctx.message.mentions[0].id
            else:
                try:
                    member_id = int(raw.strip("<@!>"))
                except ValueError:
                    return await ctx.send("❌ Mention a valid user.")

            deleted = []
            async for msg in ctx.channel.history(limit=MAX_SCAN):
                if msg.author.id == member_id:
                    deleted.append(msg)
                    if len(deleted) >= MAX_DELETE:
                        break
            if not deleted:
                return await ctx.send("🔍 No recent messages from that user.", delete_after=3)
            await ctx.channel.delete_messages(deleted)
            return await ctx.send(f"🔍 Deleted **{len(deleted)}** messages from that user.", delete_after=3)

        if arg_lower.startswith("contains "):
            keyword = arg[9:].strip().lower()
            if not keyword:
                return await ctx.send("❌ Provide a keyword.")
            deleted = []
            async for msg in ctx.channel.history(limit=MAX_SCAN):
                if keyword in msg.content.lower():
                    deleted.append(msg)
                    if len(deleted) >= MAX_DELETE:
                        break
            if not deleted:
                return await ctx.send(f"🔍 No messages found containing **'{keyword}'**.", delete_after=3)
            await ctx.channel.delete_messages(deleted)
            return await ctx.send(f"🔍 Deleted **{len(deleted)}** messages containing **'{keyword}'**.", delete_after=3)

        try:
            amount = int(arg)
        except ValueError:
            return await ctx.send(
                "❌ Invalid usage.\n"
                "`$clear <amount>`\n"
                "`$clear bots`\n"
                "`$clear user @member`\n"
                "`$clear contains <keyword>`"
            )

        if amount <= 0 or amount > 100:
            return await ctx.send("❌ Enter a number between 1 and 100.")

        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"🧹 Deleted **{len(deleted)}** messages.", delete_after=3)

    # ---------- LOCK / UNLOCK (Trial Mod+) ----------

    @commands.command()
    @has_any_mod_role()
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=_mod_embed(
            "🔒 Channel Locked",
            discord.Color.red(),
            [("📺 Channel", channel.mention), ("🔧 Moderator", ctx.author.mention)]
        ))

    @commands.command()
    @has_any_mod_role()
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=_mod_embed(
            "🔓 Channel Unlocked",
            discord.Color.green(),
            [("📺 Channel", channel.mention), ("🔧 Moderator", ctx.author.mention)]
        ))

    # ---------- SLOWMODE (Trial Mod+) ----------

    @commands.command()
    @has_any_mod_role()
    async def slowmode(self, ctx: commands.Context, seconds: int, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if not (0 <= seconds <= 21600):
            return await ctx.send("❌ Slowmode must be between **0** and **21600** seconds.")
        await channel.edit(slowmode_delay=seconds)
        msg = f"**{seconds}s** delay set." if seconds > 0 else "Slowmode **disabled**."
        await ctx.send(embed=_mod_embed(
            "🐢 Slowmode Updated",
            discord.Color.blurple(),
            [("📺 Channel", channel.mention), ("⏱️ Delay", msg), ("🔧 Moderator", ctx.author.mention)]
        ))

    # ---------- NICK (Trial Mod+) ----------

    @commands.command()
    @has_any_mod_role()
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nickname: str = None):
        old_nick = member.display_name
        await member.edit(nick=nickname)
        await ctx.send(embed=_mod_embed(
            "✏️ Nickname Changed",
            discord.Color.blurple(),
            [
                ("👤 Member", member.mention),
                ("📛 Before", old_nick),
                ("📛 After", nickname or "*reset*"),
                ("🔧 Moderator", ctx.author.mention),
            ]
        ))

    # ---------- USERINFO (Trial Mod+) ----------

    @commands.command(aliases=["ui", "whois"])
    @has_any_mod_role()
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        roles = [r.mention for r in member.roles[1:]] or ["None"]

        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color if member.color.value else discord.Color.blurple(),
            timestamp=datetime.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 ID", value=str(member.id), inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="📅 Account Created", value=discord.utils.format_dt(member.created_at, style="R"), inline=False)
        embed.add_field(name="📥 Joined Server", value=discord.utils.format_dt(member.joined_at, style="R") if member.joined_at else "Unknown", inline=False)
        embed.add_field(name=f"🎭 Roles ({len(member.roles) - 1})", value=" ".join(roles[:10]) + (" …" if len(roles) > 10 else ""), inline=False)
        warns = len(warnings.get(member.id, []))
        embed.add_field(name="⚠️ Warnings", value=str(warns), inline=True)
        embed.set_footer(text="MoonLight Moderation 🛡️")
        await ctx.send(embed=embed)

    # ---------- SERVERINFO (Trial Mod+) ----------

    @commands.command(aliases=["si", "server"])
    @has_any_mod_role()
    async def serverinfo(self, ctx: commands.Context):
        g = ctx.guild
        embed = discord.Embed(title=f"🏠 {g.name}", color=discord.Color.blurple(), timestamp=datetime.utcnow())
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="🆔 ID", value=str(g.id), inline=True)
        embed.add_field(name="👑 Owner", value=g.owner.mention if g.owner else "Unknown", inline=True)
        embed.add_field(name="👥 Members", value=str(g.member_count), inline=True)
        embed.add_field(name="📺 Channels", value=str(len(g.channels)), inline=True)
        embed.add_field(name="🎭 Roles", value=str(len(g.roles)), inline=True)
        embed.add_field(name="😀 Emojis", value=str(len(g.emojis)), inline=True)
        embed.add_field(name="📅 Created", value=discord.utils.format_dt(g.created_at, style="R"), inline=False)
        embed.set_footer(text="MoonLight Moderation 🛡️")
        await ctx.send(embed=embed)

    # ---------- SNIPE (Trial Mod+) ----------

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        sniped_messages[message.channel.id] = {
            "author": message.author,
            "content": message.content or "*[No text content]*",
            "time": datetime.utcnow(),
            "avatar": message.author.display_avatar.url,
        }

    @commands.command(aliases=["snipe"])
    @has_any_mod_role()
    async def s(self, ctx: commands.Context):
        data = sniped_messages.get(ctx.channel.id)
        if not data:
            return await ctx.send("❌ Nothing to snipe here.")

        embed = discord.Embed(
            title="🎯 Sniped Message",
            description=data["content"],
            color=discord.Color.dark_purple(),
            timestamp=data["time"],
        )
        embed.set_author(name=str(data["author"]), icon_url=data["avatar"])
        embed.set_footer(text="MoonLight Moderation • Deleted message 🛡️")
        await ctx.send(embed=embed)

    # ---------- EDIT SNIPE (Trial Mod+) ----------

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content:
            return
        edited_messages[before.channel.id] = {
            "author": before.author,
            "before": before.content or "*[No text]*",
            "after": after.content or "*[No text]*",
            "time": datetime.utcnow(),
            "avatar": before.author.display_avatar.url,
        }

    @commands.command(aliases=["esnipe", "editsnipe"])
    @has_any_mod_role()
    async def es(self, ctx: commands.Context):
        data = edited_messages.get(ctx.channel.id)
        if not data:
            return await ctx.send("❌ No recently edited messages here.")

        embed = discord.Embed(title="✏️ Edit Sniped", color=discord.Color.blurple(), timestamp=data["time"])
        embed.set_author(name=str(data["author"]), icon_url=data["avatar"])
        embed.add_field(name="📝 Before", value=data["before"], inline=False)
        embed.add_field(name="✏️ After", value=data["after"], inline=False)
        embed.set_footer(text="MoonLight Moderation • Edited message 🛡️")
        await ctx.send(embed=embed)

    # ---------- MODINFO ----------

    @commands.command(name="modinfo")
    @has_any_mod_role()
    async def modinfo(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🛡️ MoonLight Mod Permissions",
            description="Here's a breakdown of what each staff role can do.",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow(),
        )
        embed.add_field(
            name="🔴 Mod only — <@&1463136855414280214>",
            value=(
                "`$ban` — Permanently ban a member\n"
                "`$unban` — Unban a user by ID\n"
                "`$kick` — Kick a member\n"
                "`$softban` — Ban + unban to clear messages"
            ),
            inline=False,
        )
        embed.add_field(
            name="🟡 Trial Mod + Mod — <@&1463136855347302512> <@&1463136855414280214>",
            value=(
                "`$timeout / $mute` — Timeout a member\n"
                "`$removetimeout / $unmute` — Remove a timeout\n"
                "`$warn` — Issue a warning\n"
                "`$warnings / $warns` — View a member's warnings\n"
                "`$clearwarnings / $clearwarns` — Clear all warnings\n"
                "`$clear / $purge` — Bulk delete messages\n"
                "`$lock` — Lock a channel\n"
                "`$unlock` — Unlock a channel\n"
                "`$slowmode` — Set channel slowmode\n"
                "`$nick` — Change a member's nickname\n"
                "`$userinfo / $whois` — View member info\n"
                "`$serverinfo / $server` — View server info\n"
                "`$s / $snipe` — Snipe a deleted message\n"
                "`$es / $esnipe` — Snipe an edited message\n"
                "`$modinfo` — Show this panel\n"
                "`$newrole` — Create a new role\n"
                "`$role setposition` — Set a role's position\n"
                "`$rolename ch` — Rename a role\n"
                "`$arole` — Assign a role to a user\n"
                "`$remrole` — Remove a role from a user\n"
                "`$rolepurge` — Strip all roles from a user\n"
                "`$rolelist` — Paginated list of all roles"
            ),
            inline=False,
        )
        embed.set_footer(text="MoonLight Moderation 🛡️")
        await ctx.send(embed=embed)

    # ══════════════════════════════════════════
    #  ROLE MANAGEMENT COMMANDS (Trial Mod+)
    # ══════════════════════════════════════════

    # ---------- NEWROLE ----------

    @commands.command(name="newrole")
    @has_any_mod_role()
    async def newrole(self, ctx: commands.Context, *, name: str):
        """Create a new role with the given name."""
        if not name:
            return await ctx.send("❌ Usage: `$newrole <name>`")

        role = await ctx.guild.create_role(name=name, reason=f"Created by {ctx.author}")
        await ctx.send(embed=_mod_embed(
            "✅ Role Created",
            discord.Color.green(),
            [
                ("🎭 Role", role.mention),
                ("📛 Name", role.name),
                ("🔧 Moderator", ctx.author.mention),
            ]
        ))

    # ---------- ROLE SETPOSITION ----------

    @commands.group(name="role", invoke_without_command=True)
    @has_any_mod_role()
    async def role_group(self, ctx: commands.Context):
        """Role management group. Use `$role setposition <role> <position>`."""
        await ctx.send(
            "Usage:\n"
            "`$role setposition <@role or name> <position>` — set a role's position in the hierarchy"
        )

    @role_group.command(name="setposition")
    @has_any_mod_role()
    async def role_setposition(self, ctx: commands.Context, role: discord.Role, position: int):
        """Set a role's position in the hierarchy."""
        if position < 1:
            return await ctx.send("❌ Position must be 1 or higher.")

        max_pos = len(ctx.guild.roles) - 1
        if position > max_pos:
            return await ctx.send(f"❌ Position can't exceed **{max_pos}** (total roles in server).")

        old_pos = role.position
        await role.edit(position=position, reason=f"Position set by {ctx.author}")
        await ctx.send(embed=_mod_embed(
            "📶 Role Position Updated",
            discord.Color.blurple(),
            [
                ("🎭 Role", role.mention),
                ("📍 Before", str(old_pos)),
                ("📍 After", str(position)),
                ("🔧 Moderator", ctx.author.mention),
            ]
        ))

    # ---------- ROLENAME CH ----------

    @commands.command(name="rolename")
    @has_any_mod_role()
    async def rolename(self, ctx: commands.Context, subcommand: str, role: discord.Role, *, new_name: str):
        """Rename a role. Usage: $rolename ch <@role or name> <new name>"""
        if subcommand.lower() != "ch":
            return await ctx.send("❌ Usage: `$rolename ch <@role or name> <new name>`")
        if not new_name:
            return await ctx.send("❌ Provide a new name.")

        old_name = role.name
        await role.edit(name=new_name, reason=f"Renamed by {ctx.author}")
        await ctx.send(embed=_mod_embed(
            "✏️ Role Renamed",
            discord.Color.blurple(),
            [
                ("🎭 Role", role.mention),
                ("📛 Before", old_name),
                ("📛 After", new_name),
                ("🔧 Moderator", ctx.author.mention),
            ]
        ))

    # ---------- AROLE ----------

    @commands.command(name="arole")
    @has_any_mod_role()
    async def arole(self, ctx: commands.Context, role: discord.Role, member: discord.Member):
        """Assign a role to a user. Usage: $arole <@role or name> @user"""
        if role in member.roles:
            return await ctx.send(f"❌ {member.mention} already has {role.mention}.")

        await member.add_roles(role, reason=f"Assigned by {ctx.author}")
        await ctx.send(embed=_mod_embed(
            "✅ Role Assigned",
            discord.Color.green(),
            [
                ("🎭 Role", role.mention),
                ("👤 Member", member.mention),
                ("🔧 Moderator", ctx.author.mention),
            ]
        ))

    # ---------- REMROLE ----------

    @commands.command(name="remrole")
    @has_any_mod_role()
    async def remrole(self, ctx: commands.Context, role: discord.Role, member: discord.Member):
        """Remove a role from a user. Usage: $remrole <@role or name> @user"""
        if role not in member.roles:
            return await ctx.send(f"❌ {member.mention} doesn't have {role.mention}.")

        await member.remove_roles(role, reason=f"Removed by {ctx.author}")
        await ctx.send(embed=_mod_embed(
            "🗑️ Role Removed",
            discord.Color.orange(),
            [
                ("🎭 Role", role.mention),
                ("👤 Member", member.mention),
                ("🔧 Moderator", ctx.author.mention),
            ]
        ))

    # ---------- ROLEPURGE ----------

    @commands.command(name="rolepurge")
    @has_any_mod_role()
    async def rolepurge(self, ctx: commands.Context, member: discord.Member):
        """Strip all non-managed roles from a user. Usage: $rolepurge @user"""
        # Filter out @everyone and bot-managed roles (integrations)
        removable = [
            r for r in member.roles
            if not r.is_default() and not r.managed
        ]

        if not removable:
            return await ctx.send(f"❌ {member.mention} has no removable roles.")

        await member.remove_roles(*removable, reason=f"Role purge by {ctx.author}")
        await ctx.send(embed=_mod_embed(
            "🧹 Roles Purged",
            discord.Color.red(),
            [
                ("👤 Member", member.mention),
                ("🗑️ Removed", f"**{len(removable)}** role(s)"),
                ("🔧 Moderator", ctx.author.mention),
            ]
        ))

    # ---------- ROLELIST ----------

    @commands.command(name="rolelist")
    @has_any_mod_role()
    async def rolelist(self, ctx: commands.Context):
        """Paginated list of all roles in the server (highest → lowest)."""
        # Sort highest position first, skip @everyone
        roles = sorted(
            [r for r in ctx.guild.roles if not r.is_default()],
            key=lambda r: r.position,
            reverse=True,
        )

        if not roles:
            return await ctx.send("❌ This server has no roles.")

        # Chunk into pages of 15 roles each
        CHUNK = 15
        chunks = [roles[i:i + CHUNK] for i in range(0, len(roles), CHUNK)]
        total_pages = len(chunks)

        def make_embed(page: int) -> discord.Embed:
            chunk = chunks[page]
            lines = []
            for r in chunk:
                members = len(r.members)
                color_hex = f"#{r.color.value:06X}" if r.color.value else "#000000"
                lines.append(f"`#{r.position:>3}`  {r.mention}  ·  {members} member{'s' if members != 1 else ''}  ·  {color_hex}")

            embed = discord.Embed(
                title=f"🎭 Role List — {ctx.guild.name}",
                description="\n".join(lines),
                color=discord.Color.blurple(),
                timestamp=datetime.utcnow(),
            )
            embed.set_footer(text=f"MoonLight Moderation 🛡️  ·  Page {page + 1}/{total_pages}  ·  {len(roles)} roles total")
            return embed

        current = 0
        msg = await ctx.send(embed=make_embed(current))

        if total_pages == 1:
            return  # No need for reactions on a single page

        for emoji in ["◀️", "▶️", "❌"]:
            await msg.add_reaction(emoji)

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user.id == ctx.author.id
                and reaction.message.id == msg.id
                and str(reaction.emoji) in ["◀️", "▶️", "❌"]
            )

        while True:
            try:
                reaction, user = await ctx.bot.wait_for("reaction_add", timeout=60.0, check=check)
                emoji = str(reaction.emoji)

                if emoji == "▶️":
                    current = (current + 1) % total_pages
                elif emoji == "◀️":
                    current = (current - 1) % total_pages
                elif emoji == "❌":
                    await msg.delete()
                    return

                await msg.edit(embed=make_embed(current))

                try:
                    await msg.remove_reaction(reaction, user)
                except discord.Forbidden:
                    pass

            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except discord.Forbidden:
                    pass
                break


# ---------- SETUP ----------

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))