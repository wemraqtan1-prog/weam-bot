import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")

# ================= KEEP ALIVE =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8060)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
# ==============================================

# ================= IDS =================
FEEDBACK_CHANNEL_ID = 1458926588174532793   # قناة الأمر !feedback
VOTES_CHANNEL_ID = 1458927090341646346      # قناة التصويت
# ======================================

# ================= BOT =================
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)
# ======================================

# ================= SUGGESTION MODAL =================
class SuggestionModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Suggestion")

        self.idea = discord.ui.TextInput(
            label="Your suggestion",
            placeholder="Write your idea here",
            style=discord.TextStyle.paragraph,
            required=True
        )

        self.add_item(self.idea)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.client.get_channel(VOTES_CHANNEL_ID)

        embed = discord.Embed(
            title="💡 Suggestion",
            description=self.idea.value,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"By {interaction.user}")

        msg = await channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

        await interaction.response.send_message(
            "✅ Suggestion submitted successfully",
            ephemeral=True
        )

# ================= FEEDBACK MODAL =================
class FeedbackOnlyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Feedback")

        self.game_name = discord.ui.TextInput(
            label="Game name",
            placeholder="Enter the game name",
            required=True,
            max_length=100
        )

        self.issue = discord.ui.TextInput(
            label="What is the issue (if there is one)",
            placeholder="Describe the issue (optional)",
            style=discord.TextStyle.paragraph,
            required=False
        )

        self.solution = discord.ui.TextInput(
            label="Solution / Idea of improvement",
            placeholder="Your solution or idea (mandatory)",
            style=discord.TextStyle.paragraph,
            required=True
        )

        self.add_item(self.game_name)
        self.add_item(self.issue)
        self.add_item(self.solution)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.client.get_channel(VOTES_CHANNEL_ID)

        embed = discord.Embed(
            title="📢 Feedback",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="🎮 Game name",
            value=self.game_name.value,
            inline=False
        )
        embed.add_field(
            name="⚠️ Issue",
            value=self.issue.value or "No issue mentioned",
            inline=False
        )
        embed.add_field(
            name="💡 Solution / Idea",
            value=self.solution.value,
            inline=False
        )

        embed.set_footer(text=f"By {interaction.user}")

        msg = await channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

        await interaction.response.send_message(
            "✅ Feedback submitted successfully",
            ephemeral=True
        )

# ================= VIEW =================
class FeedbackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Suggestion",
        style=discord.ButtonStyle.success,
        emoji="💡"
    )
    async def suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestionModal())

    @discord.ui.button(
        label="Feedback",
        style=discord.ButtonStyle.primary,
        emoji="📣"
    )
    async def feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FeedbackOnlyModal())

# ================= COMMAND =================
@bot.command()
async def feedback(ctx):
    if ctx.channel.id != FEEDBACK_CHANNEL_ID:
        return

    # 🔥 حذف أي رسالة Feedback قديمة من البوت
    async for msg in ctx.channel.history(limit=20):
        if msg.author == bot.user and msg.embeds:
            if msg.embeds[0].title == "📢 Feedback":
                await msg.delete()

    embed = discord.Embed(
        title="📢 Feedback",
        description=(
            "Let us know your thoughts!\n\n"
            "💡 **Suggestion** – Share ideas\n"
            "📝 **Feedback** – General feedback\n\n"
            "📌 Please choose an option below."
        ),
        color=discord.Color.dark_gray()
    )

    await ctx.send(embed=embed, view=FeedbackView())


# ================= READY =================
@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")

    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if channel:
        async for msg in channel.history(limit=30):
            if msg.author == bot.user and msg.embeds:
                if msg.embeds[0].title == "📢 Feedback":
                    await msg.delete()


# ================= REACTIONS CONTROL =================
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if reaction.message.channel.id != VOTES_CHANNEL_ID:
        return

    if str(reaction.emoji) not in ["👍", "👎"]:
        await reaction.remove(user)
        return

    for r in reaction.message.reactions:
        if r.emoji != reaction.emoji:
            async for u in r.users():
                if u.id == user.id:
                    await r.remove(user)

# ================= RUN =================
bot.run(TOKEN)

