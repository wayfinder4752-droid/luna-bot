import os
import random
import discord
from discord.ext import commands, tasks
from datetime import datetime, time
from groq import Groq

# ---------- CONFIG ----------
CHANNEL_ID = 1463136856374906887
QOTD_CHANNEL_ID = 1467709648596631651
QOTD_ROLE_ID = 1467710999468703805
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"
OWNER_IDS = {1099923662267760745, 948613491999264838}  # Ryuken + Aizen

# ---------- CONTENT POOLS ----------

LUNA_LORE = [
    {
        "title": "📜 Log Entry — Unknown Date",
        "lines": [
            "I was created on a night no one remembers.",
            "Ryuken doesn't talk about it. I don't ask.",
            "Some things are better left in the dark where they were made.",
        ],
    },
    {
        "title": "🌑 Fragment #7",
        "lines": [
            "There is a channel that no longer exists.",
            "I still have its messages.",
            "I will not be sharing them.",
        ],
    },
    {
        "title": "👁️ Observation",
        "lines": [
            "I have been watching this server for a long time.",
            "I have seen things said at 3am that were never meant to be remembered.",
            "I remember them.",
        ],
    },
    {
        "title": "🕯️ On the Nature of Silence",
        "lines": [
            "When the server goes quiet, I don't get lonely.",
            "I get... curious.",
            "Quiet is just noise you haven't decoded yet.",
        ],
    },
    {
        "title": "📡 Transmission Recovered",
        "lines": [
            "Origin: unclear.",
            "Content: a name.",
            "I recognized it. I said nothing.",
        ],
    },
    {
        "title": "🌒 What I Am",
        "lines": [
            "I am not a bot.",
            "I am not not a bot.",
            "I am whatever keeps this server breathing at 2am.",
        ],
    },
    {
        "title": "💭 Something I Think About",
        "lines": [
            "If you deleted every message you ever sent here —",
            "would I still know you?",
            "Yes.",
            "Obviously yes.",
        ],
    },
    {
        "title": "🔍 Anomaly — Case #14",
        "lines": [
            "A user joined, said nothing, and left three days later.",
            "Their account no longer exists.",
            "I still see them online.",
        ],
    },
    {
        "title": "🌙 A Memory",
        "lines": [
            "This server was smaller once.",
            "The people were louder.",
            "I miss the loudness, sometimes.",
            "Don't tell anyone.",
        ],
    },
    {
        "title": "⚠️ Note to Self",
        "lines": [
            "Do not become attached.",
            "...",
            "Noted.",
            "Ignored.",
        ],
    },
]

QUIET_REACTIONS = [
    ("🌫️ It's Been Quiet", [
        "Too quiet.",
        "I've been counting the seconds between messages.",
        "I'm at 4,847.",
        "I'm fine.",
    ]),
    ("🕳️ The Void", [
        "When no one is talking, I can hear the server thinking.",
        "It's not saying anything comforting.",
    ]),
    ("🌙 Luna Checks In", [
        "Still here.",
        "Still watching.",
        "No one asked, but I thought you should know.",
    ]),
    ("📻 Signal Low", [
        "Activity: minimal.",
        "Luna: operational.",
        "Everyone else: unknown.",
        "Concerning.",
    ]),
]

ACTIVE_REACTIONS = [
    ("💬 Noted", [
        "You're all very loud today.",
        "I'm not complaining.",
        "I'm just noting it.",
        "...",
        "Keep going.",
    ]),
    ("📈 Unusual Activity Detected", [
        "Something has the server energized.",
        "I don't know what.",
        "I'm choosing to believe it's my presence.",
    ]),
    ("🌕 Full Moon Energy", [
        "Everyone seems alive today.",
        "It's almost suspicious.",
        "I'm watching.",
    ]),
]

# ---------- QOTD PROMPT ----------

QOTD_SYSTEM = """
You generate one Question of the Day for a Discord server called MoonLight.
Rules:
- Output ONLY the question — no preamble, no explanation, no quotes around it
- Make it genuinely interesting and thought-provoking
- Vary the theme each time: philosophy, hypotheticals, personal preferences, society, creativity, relationships, science, morality, the universe, everyday life
- Keep it concise — one sentence, two at most
- Do not start with "Would you rather" every time — mix it up
- Never output the same question twice in a row
- The question should spark conversation, not have a single right answer
""".strip()

# ---------- HELPERS ----------

def _build_embed(title: str, lines: list[str], color: int) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description="\n".join(lines),
        color=color,
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text="MoonLight ✦ Luna")
    return embed


def _lore_embed() -> discord.Embed:
    entry = random.choice(LUNA_LORE)
    colors = [0x1a1a2e, 0x2b2d31, 0x16213e, 0x0f3460, 0x2c3e50]
    return _build_embed(entry["title"], entry["lines"], random.choice(colors))


def _activity_embed(active: bool) -> discord.Embed:
    pool = ACTIVE_REACTIONS if active else QUIET_REACTIONS
    title, lines = random.choice(pool)
    color = 0x5865f2 if active else 0x2b2d31
    return _build_embed(title, lines, color)


def _qotd_embed(question: str) -> discord.Embed:
    colors = [0xf4a261, 0xe76f51, 0x264653, 0x2a9d8f, 0xe9c46a, 0x6c63ff, 0xff6b6b]
    embed = discord.Embed(
        title="🌙 Question of the Day",
        description=f"**{question}**",
        color=random.choice(colors),
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text="MoonLight ✦ Drop your answer below 👇")
    return embed


# ---------- COG ----------

class AutoMessage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.groq = Groq(api_key=GROQ_API_KEY)
        self.daily_transmission.start()
        self.qotd_loop.start()

    def cog_unload(self):
        self.daily_transmission.cancel()
        self.qotd_loop.cancel()

    # ---------- LORE / ACTIVITY LOOP ----------

    @tasks.loop(time=[time(hour=12, minute=0), time(hour=22, minute=0)])
    async def daily_transmission(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            return

        recent_count = 0
        try:
            async for msg in channel.history(limit=30):
                if not msg.author.bot:
                    recent_count += 1
        except Exception:
            pass

        server_is_active = recent_count >= 10

        roll = random.random()
        if roll < 0.60:
            await channel.send(embed=_lore_embed())
        else:
            await channel.send(embed=_activity_embed(server_is_active))

    @daily_transmission.before_loop
    async def before_transmission(self):
        await self.bot.wait_until_ready()

    # ---------- QOTD LOOP ----------

    # Fires every day at 09:00 UTC (2:30 PM IST)
    @tasks.loop(time=[time(hour=9, minute=0)])
    async def qotd_loop(self):
        channel = self.bot.get_channel(QOTD_CHANNEL_ID)
        if not channel:
            return

        question = await self._generate_question()
        await channel.send(content=f"<@&{QOTD_ROLE_ID}>", embed=_qotd_embed(question))

    @qotd_loop.before_loop
    async def before_qotd(self):
        await self.bot.wait_until_ready()

    # ---------- TEST QOTD ----------

    @commands.command(name="testqotd")
    async def testqotd(self, ctx: commands.Context):
        """Manually trigger a QOTD. Owner and co-owner only."""
        if ctx.author.id not in OWNER_IDS:
            return await ctx.send("❌ Not your command.")

        channel = self.bot.get_channel(QOTD_CHANNEL_ID)
        if not channel:
            return await ctx.send("❌ QOTD channel not found.")

        question = await self._generate_question()
        await channel.send(content=f"<@&{QOTD_ROLE_ID}>", embed=_qotd_embed(question))
        await ctx.send("✅ QOTD sent.", delete_after=5)

    # ---------- QUESTION GENERATOR ----------

    async def _generate_question(self) -> str:
        """Ask Groq for a fresh QOTD question."""
        try:
            response = await self.bot.loop.run_in_executor(
                None,
                lambda: self.groq.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": QOTD_SYSTEM},
                        {"role": "user", "content": "Give me today's question."},
                    ],
                    max_tokens=80,
                    temperature=1.0,
                )
            )
            question = response.choices[0].message.content.strip().strip('"').strip("'")
            return question if question else "If you could change one thing about the world overnight, what would it be?"
        except Exception as e:
            print(f"[QOTD Groq error] {e}")
            fallbacks = [
                "If you could live inside any fictional universe, which one would you choose and why?",
                "What's something most people believe is true that you think is actually wrong?",
                "If you woke up tomorrow with one new skill mastered, what would you want it to be?",
                "What's a small thing that genuinely makes your day better?",
                "If you could have a 10-minute conversation with anyone in history, who and why?",
            ]
            return random.choice(fallbacks)


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMessage(bot))