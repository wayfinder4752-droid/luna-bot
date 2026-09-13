import asyncio
import random
import time
from typing import Final

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

from moonlight.database import (
    get_balance,
    set_balance,
    get_last_daily,
    set_daily as db_set_daily,
    get_top_balances,
)

# ---------- CONSTANTS ----------

MAX_BET: Final = 250_000
DAILY_MIN: Final = 5_000
DAILY_MAX: Final = 15_000
DAILY_COOLDOWN: Final = 86_400  # 24 hours in seconds

CURRENCY: Final = "MoonShards"
COIN_EMOJI: Final = "<a:coinflip:1464991352147410944>"

CARD_VALUES: Final[dict[str, int]] = {
    "A": 11,
    "2": 2,  "3": 3,  "4": 4,  "5": 5,  "6": 6,
    "7": 7,  "8": 8,  "9": 9,  "10": 10,
    "J": 10, "Q": 10, "K": 10,
}
CARDS: Final = list(CARD_VALUES.keys())

SUIT_ICONS: Final = ["♠️", "♥️", "♦️", "♣️"]

# Wheel outcomes: (label, multiplier)
WHEEL_OUTCOMES: Final = [
    ("💀 Total disaster!", -4),
    ("😬 Bad spin",        -2),
    ("😐 Weak spin",       -1),
    ("🍀 Lucky spin!",      1),
    ("🔥 Great spin!",      2),
    ("💎 JACKPOT!",         4),
]

# Fish outcomes: (label, multiplier)
FISH_OUTCOMES: Final = [
    ("💀 You fished up literal trash. x4 loss", -4),
    ("😬 A soggy boot. x2 loss",                -2),
    ("🐟 Small fish! x1 profit",                 1),
    ("🐠 Nice catch! x2 profit",                 2),
    ("🦈 BIG FISH! x3 profit",                   3),
    ("🐋 LEGENDARY CATCH! x4 profit",            4),
]

# Slots symbols: (symbol, weight, multiplier)
SLOTS_REELS: Final = [
    ("🍋", 30, 1.5),
    ("🍒", 25, 2),
    ("🔔", 20, 2.5),
    ("⭐", 15, 3),
    ("💎", 7,  5),
    ("🌙", 3,  10),
]

# ---------- ACTIVE GAME STORES ----------
blackjack_games: dict[int, dict] = {}


# ---------- HELPERS ----------

def hand_value(hand: list[str]) -> int:
    value = sum(CARD_VALUES[c] for c in hand)
    aces = hand.count("A")
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value


def validate_bet(amount: int, balance: int, max_bet: int = MAX_BET) -> str | None:
    """Returns an error string or None if valid."""
    if amount <= 0:
        return "❌ Enter a positive amount."
    if amount > max_bet:
        return f"❌ Max bet is **{max_bet:,} {CURRENCY}**."
    if amount > balance:
        return f"❌ You don't have enough {CURRENCY}."
    return None


def balance_bar(balance: int, max_display: int = 250_000) -> str:
    """Visual balance bar for embeds."""
    filled = min(10, round((balance / max_display) * 10))
    return "🟣" * filled + "⬛" * (10 - filled)


def spin_slots() -> tuple[list[str], float]:
    """
    Spins 3 slot reels using weighted random selection.
    Returns (symbols, multiplier). Multiplier 0 = loss.
    """
    symbols = [s for s, _, _ in SLOTS_REELS]
    weights = [w for _, w, _ in SLOTS_REELS]
    mult_map = {s: m for s, _, m in SLOTS_REELS}

    result = random.choices(symbols, weights=weights, k=3)

    if result[0] == result[1] == result[2]:
        return result, mult_map[result[0]]
    elif result[0] == result[1] or result[1] == result[2]:
        return result, 0.5  # partial match
    else:
        return result, 0.0  # loss


# ---------- COG ----------

class Gambling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- PING ----------

    @commands.command()
    async def ping(self, ctx: commands.Context):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! **{latency}ms**")

    # ---------- BALANCE ----------

    @commands.command(aliases=["bal", "networth", "wallet"])
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        user = member or ctx.author
        bal = get_balance(user.id)

        embed = discord.Embed(
            title="💰 Moonlight Wallet",
            color=discord.Color.purple(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 User", value=user.mention, inline=True)
        embed.add_field(name="🏠 Server", value=ctx.guild.name, inline=True)
        embed.add_field(
            name="💎 Balance",
            value=f"**{bal:,} {CURRENCY}**\n{balance_bar(bal)}",
            inline=False,
        )
        embed.set_footer(
            text="MoonLight Economy 🌙",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
        )
        await ctx.send(embed=embed)

    # ---------- PAY ----------

    @commands.command(aliases=["transfer", "give"])
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
        if member.bot:
            return await ctx.send("🤖 You can't send MoonShards to bots.")
        if member.id == ctx.author.id:
            return await ctx.send("❌ You can't pay yourself.")

        sender_bal = get_balance(ctx.author.id)
        err = validate_bet(amount, sender_bal, max_bet=sender_bal)
        if err:
            return await ctx.send(err)

        set_balance(ctx.author.id, sender_bal - amount)
        set_balance(member.id, get_balance(member.id) + amount)

        embed = discord.Embed(
            title="🌙 MoonShards Transfer",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="📤 From", value=ctx.author.mention, inline=True)
        embed.add_field(name="📥 To", value=member.mention, inline=True)
        embed.add_field(name="💸 Amount", value=f"**{amount:,} {CURRENCY}**", inline=False)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="MoonLight Economy • Secure Transfer 🌙")
        await ctx.send(embed=embed)

    # ---------- DAILY ----------

    @commands.command()
    async def daily(self, ctx: commands.Context):
        user_id = ctx.author.id
        now = int(time.time())

        get_balance(user_id)  # ensure row exists
        last = get_last_daily(user_id)
        remaining = DAILY_COOLDOWN - (now - last)

        if remaining > 0:
            h, rem = divmod(remaining, 3600)
            m, _ = divmod(rem, 60)
            embed = discord.Embed(
                description=f"⏳ Come back in **{h}h {m}m** 🌙",
                color=discord.Color.red(),
            )
            return await ctx.send(embed=embed)

        reward = random.randint(DAILY_MIN, DAILY_MAX)
        new_bal = get_balance(user_id) + reward
        set_balance(user_id, new_bal)
        db_set_daily(user_id, timestamp=now)

        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=f"**+{reward:,} {CURRENCY}** added to your wallet!",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="💰 New Balance",
            value=f"**{new_bal:,} {CURRENCY}**\n{balance_bar(new_bal)}",
            inline=False,
        )
        embed.set_footer(text="MoonLight Economy • Come back tomorrow 🌙")
        await ctx.send(embed=embed)

    # ---------- ADD MONEY (OWNER) ----------

    @commands.command()
    async def addmoney(self, ctx: commands.Context, amount: int = 0, member: discord.Member = None):
        if ctx.author.id != 1099923662267760745:
            return await ctx.send("❌ You don't have permission to use this.")
        target = member or ctx.author
        if amount <= 0:
            return await ctx.send("❌ Amount must be positive.")

        new_bal = get_balance(target.id) + amount
        set_balance(target.id, new_bal)

        embed = discord.Embed(
            title="💸 Admin Grant",
            description=f"**+{amount:,} {CURRENCY}** → {target.mention}",
            color=discord.Color.gold(),
        )
        embed.add_field(name="💰 New Balance", value=f"**{new_bal:,}**", inline=False)
        await ctx.send(embed=embed)

    # ---------- LEADERBOARD ----------

    @commands.command(aliases=["lb", "top", "rich"])
    async def leaderboard(self, ctx: commands.Context):
        top = get_top_balances(10)
        if not top:
            return await ctx.send("❌ No data yet.")

        embed = discord.Embed(
            title="🏆 MoonShards Leaderboard",
            description="The richest players in the Moonlight 🌙",
            color=discord.Color.gold(),
        )
        medals = ["🥇", "🥈", "🥉"]

        for i, (uid, bal) in enumerate(top):
            medal = medals[i] if i < 3 else f"`#{i+1}`"
            user = self.bot.get_user(uid)
            if not user:
                try:
                    user = await self.bot.fetch_user(uid)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    user = None
            name = user.name if user else f"Unknown ({uid})"
            embed.add_field(
                name=f"{medal} {name}",
                value=f"💰 `{bal:,} {CURRENCY}`",
                inline=False,
            )

        embed.set_footer(text="MoonLight Economy • Play responsibly 🌌")
        await ctx.send(embed=embed)

    # ---------- COINFLIP ----------

    @commands.command(aliases=["cf"])
    @commands.cooldown(1, 8, BucketType.user)
    async def coinflip(self, ctx: commands.Context, amount: int, choice: str = "h"):
        user_id = ctx.author.id
        balance = get_balance(user_id)
        choice = choice.lower()

        if choice not in ("h", "t"):
            return await ctx.send("❌ Use `$cf <amount> h` or `$cf <amount> t`")

        err = validate_bet(amount, balance)
        if err:
            return await ctx.send(err)

        bet_label = "Heads" if choice == "h" else "Tails"

        embed = discord.Embed(
            title=f"{COIN_EMOJI} Flipping...",
            description=f"🎯 You bet on **{bet_label}**",
            color=discord.Color.blurple(),
        )
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(1.8)

        result = random.choice(("h", "t"))
        landed = "Heads" if result == "h" else "Tails"
        won = choice == result

        new_bal = balance + amount if won else balance - amount
        set_balance(user_id, new_bal)

        result_embed = discord.Embed(
            title=f"🪙 {landed}!",
            description=f"🎯 You bet on **{bet_label}**\n{'🎉 You **WON**!' if won else '💀 You **LOST**...'}",
            color=discord.Color.green() if won else discord.Color.red(),
        )
        result_embed.add_field(
            name="📊 Change",
            value=f"{'+'if won else '-'}{amount:,} {CURRENCY}",
            inline=True,
        )
        result_embed.add_field(
            name="💰 Balance",
            value=f"**{new_bal:,}**",
            inline=True,
        )
        result_embed.set_footer(text="MoonLight Casino 🌙")
        await msg.edit(embed=result_embed)

    # ---------- DICE ----------

    @commands.command(aliases=["d"])
    @commands.cooldown(1, 10, BucketType.user)
    async def dice(self, ctx: commands.Context, amount: int, n1: int, n2: int):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        err = validate_bet(amount, balance)
        if err:
            return await ctx.send(err)
        if n1 == n2:
            return await ctx.send("❌ The two guesses must be different.")
        if not (1 <= n1 <= 6 and 1 <= n2 <= 6):
            return await ctx.send("❌ Dice numbers must be between **1 and 6**.")

        loading = discord.Embed(
            title="🎲 Rolling...",
            description="The dice tumble across the table 🌙",
            color=discord.Color.blurple(),
        )
        msg = await ctx.send(embed=loading)
        await asyncio.sleep(1.8)

        guessed = {n1, n2}
        rolled = random.sample(range(1, 7), 2)
        matches = len(guessed & set(rolled))

        if matches == 2:
            delta = amount * 2
            new_bal = balance + delta
            title, color = "🔥 JACKPOT!", discord.Color.gold()
            result = f"Both numbers matched!\n🎉 **+{delta:,} {CURRENCY}**"
        elif matches == 1:
            delta = amount
            new_bal = balance + delta
            title, color = "✅ You Won!", discord.Color.green()
            result = f"One number matched!\n🎉 **+{delta:,} {CURRENCY}**"
        else:
            new_bal = balance - amount
            title, color = "💀 You Lost", discord.Color.red()
            result = f"No matches.\n❌ **-{amount:,} {CURRENCY}**"

        set_balance(user_id, new_bal)

        embed = discord.Embed(title=title, color=color)
        embed.add_field(name="🎲 Rolled", value=f"**{rolled[0]} & {rolled[1]}**", inline=True)
        embed.add_field(name="🎯 Guessed", value=f"**{n1} & {n2}**", inline=True)
        embed.add_field(name="📊 Result", value=result, inline=False)
        embed.add_field(name="💰 New Balance", value=f"`{new_bal:,} {CURRENCY}`", inline=False)
        embed.set_footer(text="MoonLight Casino 🎲")
        await msg.edit(embed=embed)

    # ---------- SPIN WHEEL ----------

    @commands.command(aliases=["spin"])
    @commands.cooldown(1, 10, BucketType.user)
    async def sw(self, ctx: commands.Context, amount: int):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        err = validate_bet(amount, balance, max_bet=100_000)
        if err:
            return await ctx.send(err)

        loading = discord.Embed(
            title="🎡 Spinning the Wheel...",
            description="The wheel spins under the Moonlight 🌙",
            color=discord.Color.blurple(),
        )
        loading.set_image(url="https://media1.tenor.com/m/7T24taTZIWQAAAAd/spinning.gif")
        msg = await ctx.send(embed=loading)
        await asyncio.sleep(2)

        label, multiplier = random.choice(WHEEL_OUTCOMES)
        won = multiplier > 0
        delta = amount * abs(multiplier)
        new_bal = balance + delta if won else balance - delta
        set_balance(user_id, new_bal)

        embed = discord.Embed(
            title="🎡 Spin Result",
            description=label,
            color=discord.Color.green() if won else discord.Color.red(),
        )
        embed.add_field(name="🎯 Bet", value=f"`{amount:,} {CURRENCY}`", inline=True)
        embed.add_field(
            name="📊 Outcome",
            value=f"{'🎉 +' if won else '💸 -'}{delta:,} {CURRENCY}",
            inline=True,
        )
        embed.add_field(name="💰 New Balance", value=f"`{new_bal:,} {CURRENCY}`", inline=False)
        embed.set_footer(text="MoonLight Casino 🌙 Spin responsibly")
        await msg.edit(embed=embed)

    # ---------- FISH ----------

    @commands.command()
    @commands.cooldown(1, 10, BucketType.user)
    async def fish(self, ctx: commands.Context, amount: int):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        err = validate_bet(amount, balance, max_bet=100_000)
        if err:
            return await ctx.send(err)

        loading = discord.Embed(
            title="🎣 Fishing...",
            description="Casting your line into the Moonlight waters 🌊",
            color=discord.Color.blurple(),
        )
        loading.set_footer(text="Will you catch treasure or trash?")
        msg = await ctx.send(embed=loading)
        await asyncio.sleep(2)

        label, multiplier = random.choice(FISH_OUTCOMES)
        won = multiplier > 0
        delta = amount * abs(multiplier)
        new_bal = balance + delta if won else balance - delta
        set_balance(user_id, new_bal)

        embed = discord.Embed(
            title="🎣 Fishing Result",
            description=label,
            color=discord.Color.green() if won else discord.Color.red(),
        )
        embed.add_field(name="🎯 Bet", value=f"`{amount:,} {CURRENCY}`", inline=True)
        embed.add_field(
            name="📊 Outcome",
            value=f"{'🎉 +' if won else '💸 -'}{delta:,} {CURRENCY}",
            inline=True,
        )
        embed.add_field(name="💰 New Balance", value=f"`{new_bal:,} {CURRENCY}`", inline=False)
        embed.set_footer(text="MoonLight Economy • Fish responsibly 🌙")
        await msg.edit(embed=embed)

    # ---------- SLOTS ----------

    @commands.command(aliases=["slot"])
    @commands.cooldown(1, 8, BucketType.user)
    async def slots(self, ctx: commands.Context, amount: int):
        """Pull the slot machine."""
        user_id = ctx.author.id
        balance = get_balance(user_id)

        err = validate_bet(amount, balance, max_bet=100_000)
        if err:
            return await ctx.send(err)

        loading = discord.Embed(
            title="🎰 Spinning Slots...",
            description="🎰 | ❓ ❓ ❓ | 🎰",
            color=discord.Color.blurple(),
        )
        msg = await ctx.send(embed=loading)
        await asyncio.sleep(2)

        reels, multiplier = spin_slots()
        display = " | ".join(reels)

        won = multiplier > 0
        if won:
            delta = int(amount * multiplier)
            new_bal = balance + delta
            if multiplier >= 5:
                title, color = "🌙 MOONSHOT JACKPOT!", discord.Color.gold()
            elif multiplier >= 3:
                title, color = "💎 Big Win!", discord.Color.green()
            elif multiplier == 0.5:
                title, color = "😐 Partial Match", discord.Color.blurple()
            else:
                title, color = "✅ You Won!", discord.Color.green()
            outcome = f"🎉 **+{delta:,} {CURRENCY}**"
        else:
            new_bal = balance - amount
            title, color = "💀 No Match", discord.Color.red()
            outcome = f"💸 **-{amount:,} {CURRENCY}**"

        set_balance(user_id, new_bal)

        embed = discord.Embed(title=title, color=color)
        embed.add_field(name="🎰 Reels", value=f"**{display}**", inline=False)
        embed.add_field(name="📊 Outcome", value=outcome, inline=True)
        embed.add_field(name="💰 New Balance", value=f"`{new_bal:,} {CURRENCY}`", inline=True)
        embed.set_footer(text="MoonLight Casino • Try your luck 🌙")
        await msg.edit(embed=embed)

    # ---------- ROB ----------

    @commands.command()
    @commands.cooldown(1, 60, BucketType.user)
    async def rob(self, ctx: commands.Context, target: discord.Member):
        """Attempt to rob another user. High risk, high reward."""
        if target.bot:
            return await ctx.send("🤖 You can't rob a bot.")
        if target.id == ctx.author.id:
            return await ctx.send("💀 You can't rob yourself.")

        robber_bal = get_balance(ctx.author.id)
        victim_bal = get_balance(target.id)

        if victim_bal < 500:
            return await ctx.send(f"💀 {target.mention} is too broke to rob.")
        if robber_bal < 1000:
            return await ctx.send("❌ You need at least **1,000** to attempt a robbery.")

        # 40% success rate
        success = random.random() < 0.4
        stolen = random.randint(100, min(5000, victim_bal // 4))
        fine = random.randint(500, 2000)

        if success:
            set_balance(ctx.author.id, robber_bal + stolen)
            set_balance(target.id, victim_bal - stolen)
            embed = discord.Embed(
                title="🦹 Robbery Successful!",
                description=f"You slipped away with **{stolen:,} {CURRENCY}** from {target.mention}.",
                color=discord.Color.green(),
            )
            embed.add_field(name="💰 Your Balance", value=f"`{robber_bal + stolen:,}`", inline=True)
        else:
            new_robber_bal = max(0, robber_bal - fine)
            set_balance(ctx.author.id, new_robber_bal)
            embed = discord.Embed(
                title="🚨 Caught!",
                description=f"You got caught trying to rob {target.mention} and paid a **{fine:,} {CURRENCY}** fine.",
                color=discord.Color.red(),
            )
            embed.add_field(name="💰 Your Balance", value=f"`{new_robber_bal:,}`", inline=True)

        embed.set_footer(text="MoonLight Casino • Crime doesn't always pay 🌙")
        await ctx.send(embed=embed)

    # ---------- BLACKJACK ----------

    @commands.command(aliases=["blackjack"])
    async def bj(self, ctx: commands.Context, amount: int):
        user_id = ctx.author.id
        balance = get_balance(user_id)

        err = validate_bet(amount, balance)
        if err:
            return await ctx.send(err)
        if user_id in blackjack_games:
            return await ctx.send("❌ Finish your current blackjack game first.")

        player = random.sample(CARDS, 2)
        dealer = random.sample(CARDS, 2)
        pval = hand_value(player)

        embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.blurple())
        embed.add_field(
            name="🧍 Your Hand",
            value=f"`{' '.join(player)}` → **{pval}**",
            inline=False,
        )
        embed.add_field(
            name="🤵 Dealer",
            value=f"`{dealer[0]}` ❓",
            inline=False,
        )
        embed.add_field(
            name="💰 Bet",
            value=f"`{amount:,} {CURRENCY}`",
            inline=False,
        )
        embed.set_footer(text="🟢 Hit  |  🛑 Stand  |  ⚡ Double Down")

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🟢")
        await msg.add_reaction("🛑")
        await msg.add_reaction("⚡")

        blackjack_games[user_id] = {
            "amount": amount,
            "player": player,
            "dealer": dealer,
            "message_id": msg.id,
            "doubled": False,
        }

        # Auto-check for natural blackjack
        if pval == 21:
            await self._resolve_blackjack(user_id, msg, ctx.guild)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        game = blackjack_games.get(user.id)
        if not game or reaction.message.id != game["message_id"]:
            return

        try:
            await reaction.remove(user)
        except Exception:
            pass

        player = game["player"]
        dealer = game["dealer"]
        bet = game["amount"]
        emoji = str(reaction.emoji)

        # ⚡ DOUBLE DOWN
        if emoji == "⚡" and not game["doubled"]:
            balance = get_balance(user.id)
            if balance < bet:
                return  # silently fail if can't afford
            game["amount"] = bet * 2
            game["doubled"] = True
            player.append(random.choice(CARDS))
            await self._resolve_blackjack(user.id, reaction.message, reaction.message.guild)
            return

        # 🟢 HIT
        if emoji == "🟢":
            player.append(random.choice(CARDS))
            value = hand_value(player)

            if value >= 21:
                await self._resolve_blackjack(user.id, reaction.message, reaction.message.guild)
                return

            embed = reaction.message.embeds[0]
            embed.set_field_at(
                0,
                name="🧍 Your Hand",
                value=f"`{' '.join(player)}` → **{value}**",
                inline=False,
            )
            await reaction.message.edit(embed=embed)
            return

        # 🛑 STAND
        if emoji == "🛑":
            await self._resolve_blackjack(user.id, reaction.message, reaction.message.guild)

    async def _resolve_blackjack(
        self,
        user_id: int,
        message: discord.Message,
        guild: discord.Guild,
    ) -> None:
        """Dealer plays out and resolves the blackjack game."""
        game = blackjack_games.pop(user_id, None)
        if not game:
            return

        player = game["player"]
        dealer = game["dealer"]
        bet = game["amount"]

        while hand_value(dealer) < 17:
            dealer.append(random.choice(CARDS))

        p = hand_value(player)
        d = hand_value(dealer)
        balance = get_balance(user_id)

        natural_bj = p == 21 and len(player) == 2

        if p > 21:
            new_bal = balance - bet
            title, color = "💀 Bust!", discord.Color.red()
            result = f"❌ **-{bet:,} {CURRENCY}**"
        elif natural_bj and d != 21:
            payout = int(bet * 1.5)
            new_bal = balance + payout
            title, color = "🌙 Blackjack! Natural 21!", discord.Color.gold()
            result = f"🎉 **+{payout:,} {CURRENCY}** (1.5x)"
        elif d > 21 or p > d:
            new_bal = balance + bet
            title, color = "🎉 You Win!", discord.Color.green()
            result = f"✅ **+{bet:,} {CURRENCY}**"
        elif p == d:
            new_bal = balance
            title, color = "😐 Push — Tie", discord.Color.blurple()
            result = "Bet returned."
        else:
            new_bal = balance - bet
            title, color = "💀 Dealer Wins", discord.Color.red()
            result = f"❌ **-{bet:,} {CURRENCY}**"

        set_balance(user_id, new_bal)

        embed = discord.Embed(title=title, color=color)
        embed.add_field(
            name="🧍 Your Hand",
            value=f"`{' '.join(player)}` → **{p}**",
            inline=True,
        )
        embed.add_field(
            name="🤵 Dealer Hand",
            value=f"`{' '.join(dealer)}` → **{d}**",
            inline=True,
        )
        embed.add_field(name="📊 Result", value=result, inline=False)
        embed.add_field(name="💰 New Balance", value=f"`{new_bal:,} {CURRENCY}`", inline=False)
        embed.set_footer(text="MoonLight Casino 🃏")
        await message.edit(embed=embed)


# ---------- SETUP ----------

async def setup(bot: commands.Bot):
    await bot.add_cog(Gambling(bot))