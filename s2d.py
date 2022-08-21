import os
import pathlib
from typing import Union

import discord
from dotenv import load_dotenv

import slack2discord

load_dotenv()

bot = discord.Bot()

datadir = pathlib.Path(os.getenv("EXPORTED_DATA_DIR"))
filesdir = pathlib.Path(os.getenv("FILES_DIR"))

print(f"EXPORTED_DATA_DIR: {datadir.name}")
print(f"FILES_DIR: {filesdir.name}")

slackdata = slack2discord.SlackData(datadir, filesdir)

print("USERS")
for i, user in enumerate(slackdata.users):
    print(f"{i+1}. {user.display_name}")

print("CHANNELS")
for i, ch in enumerate(slackdata.channels):
    print(f"{i+1}. {ch.id} {ch.name}")

print("Parse Messages")
slackdata.parse_all_messages()

selectmenu = slack2discord.make_select_channel(slackdata)


async def send_message(
    message: slack2discord.model.Message,
    slack_channel: slack2discord.model.Channel,
    discord_channel: Union[discord.TextChannel, discord.Thread],
):
    if message.is_reply:
        pass
    else:
        discord_files = message.get_discord_files()
        if discord_files:
            discord_msg = await discord_channel.send(
                message.to_text(), files=discord_files
            )
        else:
            discord_msg = await discord_channel.send(message.to_text())
        if message.has_thread:
            discord_thread = await discord_msg.create_thread(name="Replies")
            for reply in slack_channel.messages.find_replies_by_message(message):
                reply_files = reply.get_discord_files()
                if reply_files:
                    await discord_thread.send(reply.to_text(), files=reply_files)
                else:
                    await discord_thread.send(reply.to_text())


class S2D(discord.ui.View):
    @selectmenu
    async def restore(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        slack_ch = slackdata.channels.get_channel_by_id(select.values[0])
        discord_ch = bot.get_channel(interaction.channel_id)
        print(f"Restore slack/#{slack_ch.name} -> discord/#{discord_ch.name}")
        await interaction.response.send_message(
            f"Restore slack/#{slack_ch.name} -> discord/#{discord_ch.name}"
        )
        # Set Topic
        await discord_ch.edit(topic=slack_ch.topic)
        # Restore Mesages
        for message in slack_ch.messages:
            await send_message(
                message, slack_channel=slack_ch, discord_channel=discord_ch
            )
        print("Restore completed!")


@bot.command(description="Restore the selected slack channel")
async def restore(ctx):
    await ctx.send("Select channel", view=S2D())


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")


bot.run(os.getenv("TOKEN"))
