import asyncio
import discord
from discord.ext import commands
from datetime import datetime


# ---------- PAGE DEFINITIONS ----------

def build_pages(bot: commands.Bot) -> list[discord.Embed]:

    def page(title: str, description: str, color: int, fields: list[tuple[str, str]]) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow(),
        )
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        return embed

    # Shared divider for visual breathing room
    DIV = "▸"

    pages = [

        # 0 — Overview
        page(
            "🌙 Luna — Command Index",
            (
                "```\n"
                "  ◀️ ▶️  Navigate      1️⃣–9️⃣  Jump to page      ❌  Close\n"
                "```\n"
                "> All commands use the **`$`** prefix\n"
                "> Luna also responds to her **name** or **message replies** — no prefix needed\n"
                "> Some commands require **staff roles** — see page **5** for details"
            ),
            0x9b59b6,
            [
                (
                    "📋  Pages at a Glance",
                    (
                        f"**1️⃣  🎭 Fun**\n{DIV} `$luna` `$fortune` `$cosmic` `$luck` `$comfort` `$prophecy` `$8ball` `$rate` `$roast` `$compliment` `$moonfact`\n\n"
                        f"**2️⃣  💞 Social**\n{DIV} `$ship` `$marry` `$divorce` `$spouse` `$confess`\n\n"
                        f"**3️⃣  💰 Economy**\n{DIV} `$balance` `$daily` `$pay` `$leaderboard`\n\n"
                        f"**4️⃣  🎰 Gambling**\n{DIV} `$dice` `$cf` `$bj` `$sw` `$fish` `$slots` `$rob`\n\n"
                        f"**5️⃣  🛡️ Moderation**\n{DIV} `$kick` `$ban` `$softban` `$timeout` `$warn` `$clear` `$lock` `$snipe` `$modinfo` `$newrole` `$arole` `$remrole` `$rolepurge` `$rolelist`\n\n"
                        f"**6️⃣  ⚙️ Utility**\n{DIV} `$hug` `$kiss` `$punch` `$slap` `$pat` `$poke` `$bite` `$wave` `$kill` `$afk` `$av` `$quote`\n\n"
                        f"**7️⃣  🤖 AI**\n{DIV} `$ai disable ch` `$ai enable ch` `$disable ai` `$enable ai` `$testqotd`\n\n"
                        f"**8️⃣  📊 Statistics**\n{DIV} `$activity` `$messages` `$voicetop` `$globalstats` `$compare` `$flex` `$resetstatus` `$manualreset` `$setresetchannel`\n\n"
                        f"**9️⃣  🏰 Clans**\n{DIV} `$clan create` `$clan invite` `$clan promote` `$clan demote` `$clan kick` `$clan leave` `$clan delete` `$clan deposit` `$clan info` `$clan leaderboard`"
                    )
                ),
                (
                    "⚡  Quick Jump",
                    (
                        "`$help fun` · `$help social` · `$help economy` · `$help gambling`\n"
                        "`$help mod` · `$help utility` · `$help ai` · `$help stats` · `$help clans`\n"
                        "─────────────────────────────\n"
                        "*Reactions time out after **90 seconds** of inactivity.*"
                    )
                ),
            ]
        ),

        # 1 — Fun
        page(
            "🎭  Fun Commands",
            "> Chaotic, personality-driven, and very Luna.\n> Available to **everyone** — no restrictions.",
            0x9b59b6,
            [
                ("`$luna`",               f"{DIV} Luna's origin story. The lore is real. Read it at least once."),
                ("`$fortune`",            f"{DIV} Luna reads your fortune. Cryptic, unsettling, and somehow always accurate."),
                ("`$moonfact`",           f"{DIV} A random fact about the Moon. Genuinely educational. Luna approves."),
                ("`$cosmic`",             f"{DIV} Luna reads your cosmic energy for today. Results may be disturbing."),
                ("`$luck`",               f"{DIV} Your luck rating for today, complete with a visual bar. Don't blame Luna for the outcome."),
                ("`$comfort`",            f"{DIV} Luna says something kind. She means every word."),
                ("`$prophecy`",           f"{DIV} A prophecy is delivered. It will happen. Luna doesn't know when."),
                ("`$8ball <question>`",   f"{DIV} Ask the oracle anything. It speaks in riddles and certainty simultaneously."),
                ("`$rate <anything>`",    f"{DIV} Luna rates whatever you throw at her, out of 10. Brutal honesty included."),
                ("`$roast [@user]`",      f"{DIV} Roast someone. The results will sting. You have been warned."),
                ("`$compliment [@user]`", f"{DIV} Give someone a genuine compliment. A rare act of kindness in this server."),
            ]
        ),

        # 2 — Social
        page(
            "💞  Social Commands",
            "> Relationships, anonymous confessions, and interpersonal chaos.\n> Available to **everyone**.",
            0xe84393,
            [
                ("`$ship [@user1] [@user2]`", f"{DIV} Calculate compatibility between two people. The algorithm is merciless."),
                ("`$marry [@user]`",          f"{DIV} Propose to someone. They have **60 seconds** to accept or reject you. Luna watches."),
                ("`$divorce`",                f"{DIV} End your current marriage. Luna witnesses it in complete silence."),
                ("`$spouse [@user]`",         f"{DIV} Check who someone is married to. Useful for drama."),
                (
                    "`$confess <text>`",
                    (
                        f"{DIV} Send an anonymous confession to the confessions channel.\n"
                        "┣ Your identity is **completely hidden** — even from staff\n"
                        "┣ Your command message is **deleted instantly**\n"
                        "┣ You'll receive a quiet DM confirming it was posted\n"
                        "┗ *30 second cooldown between confessions*"
                    )
                ),
            ]
        ),

        # 3 — Economy
        page(
            "💰  Economy Commands",
            "> Build your MoonShards empire — or watch it crumble in the gambling section.\n> Available to **everyone**.",
            0xf1c40f,
            [
                ("`$balance [@user]`",    f"{DIV} Check your MoonShards wallet, or spy on someone else's. No shame in it."),
                ("`$daily`",              f"{DIV} Claim **5,000–15,000 MoonShards** every 24 hours. Don't miss a day."),
                ("`$pay [@user] <amt>`",  f"{DIV} Transfer MoonShards to another user. Charity or bribery — Luna doesn't judge."),
                ("`$leaderboard`",        f"{DIV} The top 10 richest players on the server. Your net worth, exposed publicly."),
            ]
        ),

        # 4 — Gambling
        page(
            "🎰  Gambling Commands",
            "> High risk. Potentially higher reward.\n> Luna is not responsible for your financial decisions.",
            0xe67e22,
            [
                ("`$dice <amt> <n1> <n2>`", f"{DIV} Guess both dice values before they roll.\n┣ Match 1 → **+1×** · Match both → **+2×** · Miss → **−1×**"),
                ("`$cf <amt> <h/t>`",       f"{DIV} Coinflip. Heads or tails. Pure 50/50 with no house edge.\n┣ Win → **+1×** · Lose → **−1×**"),
                ("`$bj <amt>`",             f"{DIV} Blackjack. Hit 🟢 · Stand 🛑 · Double Down ⚡ — beat the dealer.\n┣ Natural 21 → **+1.5×** · Standard win → **+1×**"),
                ("`$sw <amt>`",             f"{DIV} Spin the Wheel of Fate. **Max bet: 100,000**.\n┣ Multipliers range from **−4× to +4×** — anything can happen"),
                ("`$fish <amt>`",           f"{DIV} Cast your line and see what bites. **Max bet: 100,000**.\n┣ Trash → **−4×** · Common → small gain · Legendary → **+4×**"),
                ("`$slots <amt>`",          f"{DIV} Pull the slot machine. **Max bet: 100,000**.\n┣ 🌙🌙🌙 → **+10× jackpot** · other combos → varying multipliers"),
                ("`$rob [@user]`",          f"{DIV} Attempt to rob another user.\n┣ **40% success rate** — steal up to 25% of their balance\n┗ Fail → you pay a fine instead. Choose your targets wisely."),
            ]
        ),

        # 5 — Moderation
        page(
            "🛡️  Moderation Commands",
            "> Staff-only tools, tiered by role.\n> 🔴 **Owner / Co-Owner only** · 🟡 **Trial Mod and above**",
            0xe74c3c,
            [
                ("🔴  Ban & Kick",
                    "`$kick [@user] [reason]` — Remove a member. They can rejoin.\n"
                    "`$ban [@user] [reason]` — Permanently ban a member.\n"
                    "`$unban <user_id>` — Unban by Discord ID.\n"
                    "`$softban [@user] [reason]` — Ban + unban instantly, clears recent messages."
                ),
                ("🟡  Mute & Warn",
                    "`$timeout [@user] <mins> [reason]` — Temporarily mute. Alias: `$mute`\n"
                    "`$removetimeout [@user]` — Lift an active timeout. Alias: `$unmute`\n"
                    "`$warn [@user] [reason]` — Issue a formal warning.\n"
                    "`$warnings [@user]` — View warning history. Alias: `$warns`\n"
                    "`$clearwarnings [@user]` — Wipe all warnings."
                ),
                ("🟡  Channel & Cleanup",
                    "`$clear <amt / bots / user @m / contains kw>` — Smart bulk delete with 4 modes.\n"
                    "`$lock [#channel]` — Prevent members from sending messages.\n"
                    "`$unlock [#channel]` — Restore messaging permissions.\n"
                    "`$slowmode <seconds> [#channel]` — Set slowmode. Use `0` to disable.\n"
                    "`$snipe` / `$s` — Recover last deleted message.\n"
                    "`$esnipe` / `$es` — Recover last edited message."
                ),
                ("🟡  User & Server Info",
                    "`$nick [@user] [nickname]` — Change or reset a nickname.\n"
                    "`$userinfo [@user]` — Full member profile. Aliases: `$ui` `$whois`\n"
                    "`$serverinfo` — Server-wide stats. Aliases: `$si` `$server`\n"
                    "`$modinfo` — Live role-permission breakdown for staff."
                ),
                (
                    "🟡  Role Management",
                    (
                        "`$newrole <name>` — Create a new role\n"
                        "`$role setposition <@role> <int>` — Move a role in the hierarchy\n"
                        "`$rolename ch <@role> <new name>` — Rename a role\n"
                        "`$arole <@role> @user` — Assign a role to a user\n"
                        "`$remrole <@role> @user` — Remove a role from a user\n"
                        "`$rolepurge @user` — Strip all non-managed roles from a user\n"
                        "`$rolelist` — Paginated list of all server roles"
                    )
                ),
                ("🔴  AI Toggle",
                    "`$disable ai` — Disable AI responses server-wide.\n"
                    "`$enable ai` — Re-enable AI responses server-wide."
                ),
            ]
        ),

        # 6 — Utility
        page(
            "⚙️  Utility Commands",
            "> Actions, AFK management, avatars, and quote cards.\n> Available to **everyone** unless noted.",
            0x1abc9c,
            [
                (
                    "🤝  Actions",
                    "`$hug` `$kiss` `$punch` `$slap` `$pat` `$poke` `$bite` `$wave` `$kill` — all accept `[@user]`\n"
                    f"{DIV} Each comes with a matching GIF. Luna narrates `$kill` herself."
                ),
                ("`$afk [reason]`",
                    f"{DIV} Set your AFK status with an optional reason.\n"
                    "┣ Luna notifies anyone who mentions you while you're away\n"
                    "┗ Announces your return when you next type"
                ),
                ("`$av [@user]`",     f"{DIV} Display a user's full-size avatar. Aliases: `$avatar` `$pfp`"),
                (
                    "`$quote`",
                    (
                        f"{DIV} Generate a stylized quote card posted to the quotes channel.\n"
                        "┣ `$quote <text>` — quote yourself\n"
                        "┣ `$quote @user <text>` — quote someone else\n"
                        "┣ *(reply to any message)* + `$quote` — instantly quotes that message\n"
                        "┗ *15 second cooldown · max 220 characters*"
                    )
                ),
            ]
        ),

        # 7 — AI
        page(
            "🤖  AI — Luna's Intelligence",
            "> Luna is powered by **Groq** (`llama-3.3-70b-versatile`).\n> She listens, she remembers context, and she has opinions.",
            0x5865f2,
            [
                (
                    "💬  How to Talk to Luna",
                    (
                        "No prefix needed — just say her name or reply to her:\n"
                        "```\n"
                        "luna what do you think about this?\n"
                        "hey luna, roast me\n"
                        "[reply to Luna's message] wait what did you mean\n"
                        "```"
                    )
                ),
                (
                    "⏱️  Limits",
                    (
                        "┣ **Daily limit:** 10 AI responses per user per day\n"
                        "┣ **Cooldown:** 10 seconds between responses\n"
                        "┗ **Bypassed for:** Ryuken & Aizen — always unlimited"
                    )
                ),
                (
                    "🔧  AI Controls  *(Owner & Co-Owner only)*",
                    (
                        "`$ai disable ch` — Silence Luna in the current channel only\n"
                        "`$ai enable ch` — Restore Luna's replies in the current channel\n"
                        "`$disable ai` — Disable AI responses server-wide\n"
                        "`$enable ai` — Re-enable AI responses server-wide"
                    )
                ),
                (
                    "🌙  QOTD — Question of the Day",
                    (
                        f"{DIV} Luna posts an AI-generated question every day to the QOTD channel.\n"
                        "┣ Themes rotate: philosophy, hypotheticals, morality, creativity, and more\n"
                        "┣ Pings the QOTD role automatically\n"
                        "┗ `$testqotd` — manually trigger a QOTD *(Owner & Co-Owner only)*"
                    )
                ),
            ]
        ),

        # 8 — Statistics
        page(
            "📊  Statistics Commands",
            "> Track activity, earn ranks, and see who actually runs this server.\n> Available to **everyone** unless marked 🔴.",
            0x3498db,
            [
                (
                    "`$activity [@user]`",
                    (
                        f"{DIV} Full activity profile — rank badge, message count, voice time, leaderboard position,\n"
                        "next rank progress, flavor text, and countdown to the next leaderboard reset.\n"
                        "┗ Aliases: `$stats` `$profile`"
                    )
                ),
                (
                    "`$messages`",
                    (
                        f"{DIV} Top 10 users by message count this cycle.\n"
                        "┣ Your position is highlighted even if you're outside the top 10\n"
                        "┣ Footer shows time remaining until the next reset\n"
                        "┗ Aliases: `$topmessages` `$msgstop`"
                    )
                ),
                (
                    "`$voicetop`",
                    (
                        f"{DIV} Top 10 users by total voice channel time.\n"
                        "┗ Aliases: `$vctop` `$topvoice`"
                    )
                ),
                (
                    "`$globalstats`",
                    (
                        f"{DIV} Server-wide aggregate stats: total messages, tracked users,\n"
                        "members in VC right now, average messages per user, and the most active member.\n"
                        "┗ Aliases: `$serverstats` `$ss`"
                    )
                ),
                (
                    "`$compare @user1 [@user2]`",
                    (
                        f"{DIV} Head-to-head activity duel between two members.\n"
                        "┣ Compares messages, voice time, and combined score\n"
                        "┣ Declares a winner with the point gap\n"
                        "┗ Alias: `$vs`"
                    )
                ),
                (
                    "`$flex`",
                    (
                        f"{DIV} Post a glorified brag card of your own stats with zero shame.\n"
                        "┗ Alias: `$brag`"
                    )
                ),
                (
                    "`$resetstatus`",
                    (
                        f"{DIV} Check when the message leaderboard last reset\n"
                        "┗ and how long until the next automatic reset. Alias: `$resetinfo`"
                    )
                ),
                (
                    "🔴  `$setresetchannel`",
                    (
                        f"{DIV} Set the current channel as the destination for leaderboard reset announcements.\n"
                        "┗ *Requires Administrator.*"
                    )
                ),
                (
                    "🔴  `$manualreset`",
                    (
                        f"{DIV} Immediately wipe the message leaderboard and restart the 24h timer.\n"
                        "┗ *Requires Administrator.* Alias: `$forcereset`"
                    )
                ),
            ]
        ),

        # 9 — Clans
        page(
            "🏰  Clan Commands",
            "> Build a clan, grow your vault, and dominate the leaderboard.\n> Available to **everyone** — rank restrictions apply within clans.",
            0x8e44ad,
            [
                (
                    "🏗️  Getting Started",
                    (
                        f"`$clan create <name>` — Found a new clan.\n"
                        f"┣ Costs **1,000,000 MoonShards** to create\n"
                        f"┣ Name must be **30 characters or fewer**\n"
                        f"┗ You become the **Owner** automatically"
                    )
                ),
                (
                    "📨  Membership",
                    (
                        f"`$clan invite @user` — Invite someone to your clan *(Elder+ only)*\n"
                        f"┣ Target has **60 seconds** to accept or decline\n"
                        f"`$clan kick @user` — Remove a member *(Co-Owner+ only)*\n"
                        f"`$clan leave` — Leave your current clan\n"
                        f"┗ *Owners must delete the clan instead of leaving*"
                    )
                ),
                (
                    "⬆️  Rank System",
                    (
                        f"⚪ **Member** → 🟢 **Hero** → 🔵 **Elder** → 🟣 **Co-Owner** → 👑 **Owner**\n\n"
                        f"`$clan promote @user` — Promote a member one rank *(Co-Owner+ only)*\n"
                        f"`$clan demote @user` — Demote a member one rank *(Co-Owner+ only)*\n"
                        f"┣ Only the **Owner** can promote/demote Co-Owners\n"
                        f"┗ **Elders and above** can invite new members"
                    )
                ),
                (
                    "💰  Vault & Levels",
                    (
                        f"`$clan deposit <amount>` — Deposit your MoonShards into the clan vault\n"
                        f"┣ Level = **1 + 1 per 1,000,000** MoonShards in the vault\n"
                        f"┣ A progress bar tracks your march to the next level\n"
                        f"┗ Vault balance and level are shown on your clan profile"
                    )
                ),
                (
                    "📋  Info & Leaderboard",
                    (
                        f"`$clan info [name]` — View full clan profile: vault, level, progress bar, and full roster with ranks\n"
                        f"┣ Omit the name to view your own clan\n"
                        f"`$clan leaderboard` — Top 10 clans ranked by Level → Vault → Members\n"
                        f"┗ Alias: `$clan lb`"
                    )
                ),
                (
                    "💀  Deleting a Clan",
                    (
                        f"`$clan delete` — Permanently disband the clan *(Owner only)*\n"
                        f"┣ Requires **confirmation** before deletion\n"
                        f"┗ All members are removed and nicknames are cleared"
                    )
                ),
            ]
        ),
    ]

    # Consistent footers
    labels = ["Index"] + [f"Page {i} / 9" for i in range(1, 10)]
    for i, embed in enumerate(pages):
        embed.set_footer(text=f"MoonLight  ✦  {labels[i]}  ·  ◀️ ▶️ to navigate  ·  1️⃣–9️⃣ to jump  ·  ❌ to close")

    return pages


# ---------- REACTIONS ----------
NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
NAV_EMOJIS    = ["◀️", "▶️", "❌"]
ALL_EMOJIS    = NAV_EMOJIS + NUMBER_EMOJIS


# ---------- COG ----------

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["h", "commands"])
    async def help(self, ctx: commands.Context, *, query: str = None):
        """Paginated help menu. Optionally: $help fun / social / economy / gambling / mod / utility / ai / stats"""
        pages = build_pages(self.bot)

        category_map = {
            "fun":        1,
            "social":     2,
            "economy":    3,
            "gambling":   4,
            "moderation": 5,
            "mod":        5,
            "utility":    6,
            "ai":         7,
            "stats":      8,
            "statistics": 8,
            "clans":      9,
            "clan":       9,
        }

        current = 0
        if query:
            current = category_map.get(query.lower().strip(), 0)

        msg = await ctx.send(embed=pages[current])

        for emoji in ALL_EMOJIS:
            await msg.add_reaction(emoji)

        def check(reaction: discord.Reaction, user: discord.User) -> bool:
            return (
                user.id == ctx.author.id
                and reaction.message.id == msg.id
                and str(reaction.emoji) in ALL_EMOJIS
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=90.0, check=check
                )
                emoji = str(reaction.emoji)

                if emoji == "▶️":
                    current = (current + 1) % len(pages)
                elif emoji == "◀️":
                    current = (current - 1) % len(pages)
                elif emoji == "❌":
                    await msg.delete()
                    return
                elif emoji in NUMBER_EMOJIS:
                    current = NUMBER_EMOJIS.index(emoji) + 1

                await msg.edit(embed=pages[current])

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
    await bot.add_cog(Help(bot))