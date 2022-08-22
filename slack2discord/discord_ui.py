import discord

from .slackdata import SlackData


def make_select_channel(slackdata: SlackData):
    return discord.ui.select(
        placeholder="Select Channel",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label=ch.name, value=ch.id, description=ch.topic)
            for ch in slackdata.channels
        ],
    )
