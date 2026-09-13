import asyncio
import sqlite3
import os
import discord
from discord.ext import commands
from datetime import datetime

# ---------- DB CONNECTION (inline — no import needed) ----------
DB_PATH = "/data/moonlight.db" if os.path.isdir("/data") else "moonlight.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

def _get_balance(user_id: int) -> int:
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, balance, last_daily) VALUES (?, 1000, 0)", (user_id,))
    conn.commit()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    return cur.fetchone()[0]

def _set_balance(user_id: int, amount: int) -> None:
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, balance, last_daily) VALUES (?, 1000, 0)", (user_id,))
    cur.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

# ---------- RANK HIERARCHY ----------
RANKS = ["member", "hero", "elder", "co-owner", "owner"]
RANK_EMOJI = {
    "member":   "⚪",
    "hero":     "🟢",
    "elder":    "🔵",
    "co-owner": "🟣",
    "owner":    "👑",
}

CLAN_CREATE_MIN = 1_000_000

# Superscript character map for nickname tag
SUPERSCRIPT = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ",
    "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᵀᵁᵛᵂˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖqʳˢᵗᵘᵛʷˣʸᶻ⁰¹²³⁴⁵⁶⁷⁸⁹ "
)


def to_superscript(text: str) -> str:
    return text.translate(SUPERSCRIPT)


def rank_index(rank: str) -> int:
    return RANKS.index(rank) if rank in RANKS else 0


def can_invite(rank: str) -> bool:
    return rank_index(rank) >= rank_index("elder")


def promoted_rank(current: str) -> str | None:
    idx = rank_index(current)
    if idx >= rank_index("co-owner"):
        return None
    return RANKS[idx + 1]


def demoted_rank(current: str) -> str | None:
    idx = rank_index(current)
    if idx <= 0:
        return None
    return RANKS[idx - 1]


# ---------- DB HELPERS ----------

def _get_clan_by_name(name: str) -> dict | None:
    cur = conn.cursor()
    cur.execute("SELECT id, name, leader_id, balance, level FROM clans WHERE LOWER(name) = LOWER(?)", (name,))
    row = cur.fetchone()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "leader_id": row[2], "balance": row[3], "level": row[4]}


def _get_clan_of_user(user_id: int) -> tuple[dict, str] | tuple[None, None]:
    cur = conn.cursor()
    cur.execute(
        "SELECT c.id, c.name, c.leader_id, c.balance, cm.role, c.level "
        "FROM clan_members cm JOIN clans c ON cm.clan_id = c.id "
        "WHERE cm.user_id = ?",
        (user_id,)
    )
    row = cur.fetchone()
    if not row:
        return None, None
    return {"id": row[0], "name": row[1], "leader_id": row[2], "balance": row[3], "level": row[5]}, row[4]


def _get_clan_members(clan_id: int) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute("SELECT user_id, role FROM clan_members WHERE clan_id = ?", (clan_id,))
    return cur.fetchall()


def _get_member_role(user_id: int, clan_id: int) -> str | None:
    cur = conn.cursor()
    cur.execute("SELECT role FROM clan_members WHERE user_id = ? AND clan_id = ?", (user_id, clan_id))
    row = cur.fetchone()
    return row[0] if row else None


def _create_clan(name: str, leader_id: int) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO clans (name, leader_id, balance, level) VALUES (?, ?, 0, 1)",
        (name, leader_id)
    )
    clan_id = cur.lastrowid
    cur.execute(
        "INSERT OR REPLACE INTO clan_members (user_id, clan_id, role) VALUES (?, ?, 'owner')",
        (leader_id, clan_id)
    )
    conn.commit()
    return clan_id


def _add_member(user_id: int, clan_id: int, role: str = "member") -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO clan_members (user_id, clan_id, role) VALUES (?, ?, ?)",
        (user_id, clan_id, role)
    )
    conn.commit()


def _remove_member(user_id: int) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM clan_members WHERE user_id = ?", (user_id,))
    conn.commit()


def _set_role(user_id: int, clan_id: int, role: str) -> None:
    cur = conn.cursor()
    cur.execute(
        "UPDATE clan_members SET role = ? WHERE user_id = ? AND clan_id = ?",
        (role, user_id, clan_id)
    )
    conn.commit()


def _delete_clan(clan_id: int) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM clan_members WHERE clan_id = ?", (clan_id,))
    cur.execute("DELETE FROM clans WHERE id = ?", (clan_id,))
    conn.commit()


def _update_vault(clan_id: int, amount: int, old_level: int) -> tuple[int, int]:
    """Add amount to vault, recalculate level. Returns (new_balance, new_level)."""
    cur = conn.cursor()
    cur.execute("UPDATE clans SET balance = balance + ? WHERE id = ?", (amount, clan_id))
    conn.commit()
    cur.execute("SELECT balance FROM clans WHERE id = ?", (clan_id,))
    new_balance = cur.fetchone()[0]

    # Level = 1 + 1 per million in the vault
    new_level = 1 + (new_balance // 1_000_000)

    if new_level != old_level:
        cur.execute("UPDATE clans SET level = ? WHERE id = ?", (new_level, clan_id))
        conn.commit()

    return new_balance, new_level


# ---------- NICKNAME HELPER ----------

async def _set_clan_nick(member: discord.Member, clan_name: str | None) -> None:
    try:
        base = member.display_name
        if " ⌜" in base:
            base = base[:base.rfind(" ⌜")].strip()

        if clan_name:
            sup = to_superscript(clan_name)
            new_nick = f"{base} ⌜{sup}⌝"
            while len(new_nick) > 32 and len(base) > 1:
                base = base[:-1]
                new_nick = f"{base} ⌜{sup}⌝"
        else:
            new_nick = base if base != member.name else None

        await member.edit(nick=new_nick)
    except discord.Forbidden:
        pass


# ---------- EMBED BUILDER ----------

def _clan_embed(clan: dict, members: list[tuple[int, str]], guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title=f"🏰 {clan['name']}",
        color=0x9b59b6,
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="💰 Vault", value=f"**{clan['balance']:,}** MoonShards", inline=True)
    embed.add_field(name="👥 Members", value=str(len(members)), inline=True)
    embed.add_field(name="⭐ Level", value=str(clan.get("level", 1)), inline=True)

    # Progress to next level
    vault = clan["balance"]
    current_level = clan.get("level", 1)
    progress = vault % 1_000_000
    bar_filled = int(progress / 1_000_000 * 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    embed.add_field(
        name=f"📈 Progress to Lv.{current_level + 1}",
        value=f"`{bar}` {progress:,} / 1,000,000",
        inline=False,
    )

    roster_lines = []
    for rank in reversed(RANKS):
        for uid, role in members:
            if role == rank:
                m = guild.get_member(uid)
                display = m.display_name if m else f"<@{uid}>"
                roster_lines.append(f"{RANK_EMOJI[rank]} **{display}** — {rank.capitalize()}")

    embed.add_field(
        name="📋 Roster",
        value="\n".join(roster_lines) if roster_lines else "Empty",
        inline=False,
    )
    embed.set_footer(text="MoonLight ✦ Clans")
    return embed


# ---------- COG ----------

class Clans(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- $clan GROUP ----------

    @commands.group(name="clan", invoke_without_command=True)
    async def clan(self, ctx: commands.Context):
        await ctx.send(
            "**🏰 Clan Commands**\n"
            "`$clan create <n>` — create a clan *(requires 1M MoonShards)*\n"
            "`$clan invite @user` — invite someone *(elder+ only)*\n"
            "`$clan promote @user` — promote a member\n"
            "`$clan demote @user` — demote a member\n"
            "`$clan kick @user` — kick a member\n"
            "`$clan leave` — leave your clan\n"
            "`$clan delete` — permanently delete your clan *(owner only)*\n"
            "`$clan deposit <amount>` — deposit MoonShards into the vault\n"
            "`$clan info [name]` — view clan info\n"
            "`$clan leaderboard` — top 10 clans"
        )

    # ---------- CREATE ----------

    @clan.command(name="create")
    async def clan_create(self, ctx: commands.Context, *, name: str = None):
        if not name:
            return await ctx.send("❌ Usage: `$clan create <n>`")
        if len(name) > 30:
            return await ctx.send("❌ Clan name must be 30 characters or fewer.")

        existing_clan, _ = _get_clan_of_user(ctx.author.id)
        if existing_clan:
            return await ctx.send(f"❌ You're already in **{existing_clan['name']}**. Leave first.")

        if _get_clan_by_name(name):
            return await ctx.send(f"❌ A clan named **{name}** already exists.")

        bal = _get_balance(ctx.author.id)
        if bal < CLAN_CREATE_MIN:
            return await ctx.send(
                f"❌ You need at least **1,000,000 MoonShards** to create a clan.\n"
                f"Your balance: **{bal:,}**"
            )

        _create_clan(name, ctx.author.id)
        await _set_clan_nick(ctx.author, name)

        embed = discord.Embed(
            title="🏰 Clan Created!",
            description=f"**{name}** has been founded by {ctx.author.mention}.",
            color=0x2ecc71,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text="MoonLight ✦ Clans")
        await ctx.send(embed=embed)

    # ---------- INVITE ----------

    @clan.command(name="invite")
    async def clan_invite(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Usage: `$clan invite @user`")
        if member.bot:
            return await ctx.send("❌ You can't invite bots.")
        if member.id == ctx.author.id:
            return await ctx.send("❌ You can't invite yourself.")

        clan, invoker_role = _get_clan_of_user(ctx.author.id)
        if not clan:
            return await ctx.send("❌ You're not in a clan.")
        if not can_invite(invoker_role):
            return await ctx.send("❌ Only **Elders** and above can invite members.")

        target_clan, _ = _get_clan_of_user(member.id)
        if target_clan:
            return await ctx.send(f"❌ {member.mention} is already in **{target_clan['name']}**.")

        embed = discord.Embed(
            title="📨 Clan Invitation",
            description=(
                f"{ctx.author.mention} has invited you to join **{clan['name']}**!\n\n"
                f"React with 🟢 to **accept** or 🔴 to **decline**.\n"
                f"*Expires in 60 seconds.*"
            ),
            color=0x9b59b6,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text="MoonLight ✦ Clans")
        msg = await ctx.send(content=member.mention, embed=embed)
        await msg.add_reaction("🟢")
        await msg.add_reaction("🔴")

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user.id == member.id
                and reaction.message.id == msg.id
                and str(reaction.emoji) in ["🟢", "🔴"]
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await msg.clear_reactions()
            return await ctx.send(f"⏰ Invite to {member.mention} expired.")

        await msg.clear_reactions()

        if str(reaction.emoji) == "🔴":
            return await ctx.send(f"❌ {member.mention} declined the invitation.")

        clan2, _ = _get_clan_of_user(ctx.author.id)
        if not clan2:
            return await ctx.send("❌ The clan no longer exists.")
        target_check, _ = _get_clan_of_user(member.id)
        if target_check:
            return await ctx.send(f"❌ {member.mention} joined another clan while pending.")

        _add_member(member.id, clan2["id"])
        await _set_clan_nick(member, clan2["name"])

        await ctx.send(embed=discord.Embed(
            description=f"✅ {member.mention} has joined **{clan2['name']}**!",
            color=0x2ecc71,
        ))

    # ---------- PROMOTE ----------

    @clan.command(name="promote")
    async def clan_promote(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Usage: `$clan promote @user`")
        if member.id == ctx.author.id:
            return await ctx.send("❌ You can't promote yourself.")

        clan, invoker_role = _get_clan_of_user(ctx.author.id)
        if not clan:
            return await ctx.send("❌ You're not in a clan.")
        if invoker_role not in ("owner", "co-owner"):
            return await ctx.send("❌ Only the **Owner** or **Co-Owner** can promote members.")

        target_clan, _ = _get_clan_of_user(member.id)
        if not target_clan or target_clan["id"] != clan["id"]:
            return await ctx.send(f"❌ {member.mention} is not in your clan.")

        current_role = _get_member_role(member.id, clan["id"])
        new_role = promoted_rank(current_role)

        if new_role is None:
            return await ctx.send(f"❌ {member.mention} is already at the highest promotable rank (**Co-Owner**).")
        if new_role == "co-owner" and invoker_role != "owner":
            return await ctx.send("❌ Only the **Owner** can promote to Co-Owner.")

        _set_role(member.id, clan["id"], new_role)
        await ctx.send(embed=discord.Embed(
            description=f"⬆️ {member.mention} promoted to **{new_role.capitalize()}** in **{clan['name']}**!",
            color=0x2ecc71,
        ))

    # ---------- DEMOTE ----------

    @clan.command(name="demote")
    async def clan_demote(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Usage: `$clan demote @user`")
        if member.id == ctx.author.id:
            return await ctx.send("❌ You can't demote yourself.")

        clan, invoker_role = _get_clan_of_user(ctx.author.id)
        if not clan:
            return await ctx.send("❌ You're not in a clan.")
        if invoker_role not in ("owner", "co-owner"):
            return await ctx.send("❌ Only the **Owner** or **Co-Owner** can demote members.")

        target_clan, _ = _get_clan_of_user(member.id)
        if not target_clan or target_clan["id"] != clan["id"]:
            return await ctx.send(f"❌ {member.mention} is not in your clan.")

        current_role = _get_member_role(member.id, clan["id"])
        if current_role == "owner":
            return await ctx.send("❌ The owner cannot be demoted.")
        if current_role == "co-owner" and invoker_role != "owner":
            return await ctx.send("❌ Only the **Owner** can demote a Co-Owner.")

        new_role = demoted_rank(current_role)
        if new_role is None:
            return await ctx.send(f"❌ {member.mention} is already at the lowest rank.")

        _set_role(member.id, clan["id"], new_role)
        await ctx.send(embed=discord.Embed(
            description=f"⬇️ {member.mention} demoted to **{new_role.capitalize()}** in **{clan['name']}**.",
            color=0xe74c3c,
        ))

    # ---------- KICK ----------

    @clan.command(name="kick")
    async def clan_kick(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.send("❌ Usage: `$clan kick @user`")
        if member.id == ctx.author.id:
            return await ctx.send("❌ Use `$clan leave` to leave your own clan.")

        clan, invoker_role = _get_clan_of_user(ctx.author.id)
        if not clan:
            return await ctx.send("❌ You're not in a clan.")
        if invoker_role not in ("owner", "co-owner"):
            return await ctx.send("❌ Only the **Owner** or **Co-Owner** can kick members.")

        target_clan, _ = _get_clan_of_user(member.id)
        if not target_clan or target_clan["id"] != clan["id"]:
            return await ctx.send(f"❌ {member.mention} is not in your clan.")

        target_role = _get_member_role(member.id, clan["id"])
        if target_role == "owner":
            return await ctx.send("❌ You can't kick the owner.")
        if target_role == "co-owner" and invoker_role != "owner":
            return await ctx.send("❌ Only the **Owner** can kick a Co-Owner.")

        _remove_member(member.id)
        await _set_clan_nick(member, None)
        await ctx.send(embed=discord.Embed(
            description=f"🥾 {member.mention} has been kicked from **{clan['name']}**.",
            color=0xe74c3c,
        ))

    # ---------- LEAVE ----------

    @clan.command(name="leave")
    async def clan_leave(self, ctx: commands.Context):
        clan, role = _get_clan_of_user(ctx.author.id)
        if not clan:
            return await ctx.send("❌ You're not in a clan.")
        if role == "owner":
            return await ctx.send("❌ Owners can't leave — delete the clan with `$clan delete` instead.")

        _remove_member(ctx.author.id)
        await _set_clan_nick(ctx.author, None)
        await ctx.send(embed=discord.Embed(
            description=f"👋 You've left **{clan['name']}**.",
            color=0x95a5a6,
        ))

    # ---------- DELETE ----------

    @clan.command(name="delete")
    async def clan_delete(self, ctx: commands.Context):
        clan, role = _get_clan_of_user(ctx.author.id)
        if not clan:
            return await ctx.send("❌ You're not in a clan.")
        if role != "owner":
            return await ctx.send("❌ Only the **Owner** can delete the clan.")

        members = _get_clan_members(clan["id"])

        confirm_embed = discord.Embed(
            title="⚠️ Delete Clan",
            description=(
                f"Are you sure you want to permanently delete **{clan['name']}**?\n"
                f"This will remove **{len(members)}** member(s) and cannot be undone.\n\n"
                f"React with ✅ to confirm or ❌ to cancel."
            ),
            color=0xe74c3c,
        )
        msg = await ctx.send(embed=confirm_embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user.id == ctx.author.id
                and reaction.message.id == msg.id
                and str(reaction.emoji) in ["✅", "❌"]
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await msg.clear_reactions()
            return await ctx.send("⏰ Deletion cancelled — timed out.")

        await msg.clear_reactions()
        if str(reaction.emoji) == "❌":
            return await ctx.send("✅ Deletion cancelled.")

        for uid, _ in members:
            m = ctx.guild.get_member(uid)
            if m:
                await _set_clan_nick(m, None)

        _delete_clan(clan["id"])
        await ctx.send(embed=discord.Embed(
            description=f"💀 **{clan['name']}** has been permanently deleted.",
            color=0xe74c3c,
        ))

    # ---------- DEPOSIT ----------

    @clan.command(name="deposit")
    async def clan_deposit(self, ctx: commands.Context, amount: int = None):
        if not amount or amount <= 0:
            return await ctx.send("❌ Usage: `$clan deposit <amount>`")

        clan, _ = _get_clan_of_user(ctx.author.id)
        if not clan:
            return await ctx.send("❌ You're not in a clan.")

        bal = _get_balance(ctx.author.id)
        if bal < amount:
            return await ctx.send(f"❌ You only have **{bal:,}** MoonShards.")

        old_level = clan.get("level", 1)
        _set_balance(ctx.author.id, bal - amount)
        new_vault, new_level = _update_vault(clan["id"], amount, old_level)

        leveled_up = new_level > old_level
        progress = new_vault % 1_000_000
        bar_filled = int(progress / 1_000_000 * 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)

        desc = (
            f"💰 Deposited **{amount:,}** MoonShards into **{clan['name']}**'s vault.\n"
            f"Vault: **{new_vault:,}**  ·  ⭐ Level **{new_level}**\n"
            f"`{bar}` {progress:,} / 1,000,000 to Lv.{new_level + 1}"
        )
        if leveled_up:
            desc = f"🎉 **{clan['name']} leveled up to Level {new_level}!**\n\n" + desc

        await ctx.send(embed=discord.Embed(description=desc, color=0x2ecc71 if not leveled_up else 0xf1c40f))

    # ---------- INFO ----------

    @clan.command(name="info")
    async def clan_info(self, ctx: commands.Context, *, name: str = None):
        if name:
            clan = _get_clan_by_name(name)
            if not clan:
                return await ctx.send(f"❌ No clan named **{name}** found.")
        else:
            clan, _ = _get_clan_of_user(ctx.author.id)
            if not clan:
                return await ctx.send("❌ You're not in a clan. Use `$clan info <n>` to look one up.")

        members = _get_clan_members(clan["id"])
        await ctx.send(embed=_clan_embed(clan, members, ctx.guild))

    # ---------- LEADERBOARD ----------

    @clan.command(name="leaderboard", aliases=["lb"])
    async def clan_leaderboard(self, ctx: commands.Context):
        """Top 10 clans ranked by level, then vault balance, then member count."""
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id, c.name, c.level, c.balance,
                   COUNT(cm.user_id) as member_count
            FROM clans c
            LEFT JOIN clan_members cm ON cm.clan_id = c.id
            GROUP BY c.id
            ORDER BY c.level DESC, c.balance DESC, member_count DESC
            LIMIT 10
        """)
        rows = cur.fetchall()

        if not rows:
            return await ctx.send("❌ No clans exist yet.")

        user_clan, _ = _get_clan_of_user(ctx.author.id)
        user_clan_id = user_clan["id"] if user_clan else None

        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (clan_id, name, level, balance, member_count) in enumerate(rows):
            pos = medals[i] if i < 3 else f"`#{i + 1}`"
            hl = "**" if clan_id == user_clan_id else ""
            lines.append(
                f"{pos} {hl}{name}{hl}\n"
                f"　⭐ Lv.{level}  💰 {balance:,}  👥 {member_count}"
            )

        embed = discord.Embed(
            title="🏆 Clan Leaderboard",
            description="\n\n".join(lines),
            color=0xf1c40f,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text="MoonLight ✦ Ranked by Level → Vault → Members")
        await ctx.send(embed=embed)


# ---------- SETUP ----------

async def setup(bot: commands.Bot):
    await bot.add_cog(Clans(bot))