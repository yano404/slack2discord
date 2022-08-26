import json
import os
import re
from pathlib import Path
from typing import List, Union

import discord

from . import util


class User:
    def __init__(self, userinfo: dict) -> None:
        self.id: str = userinfo["id"]
        self.name: str = userinfo["name"]
        self.display_name: str = userinfo["profile"]["display_name"]
        self.real_name: str = userinfo["profile"]["real_name"]
        # self.email = userinfo["profile"]["email"]
        if not self.display_name:
            self.display_name = self.real_name


class Users:
    def __init__(self, usersjsonpath: Union[os.PathLike, str]) -> None:
        self.userlist: List[User] = []
        with open(usersjsonpath) as f:
            usersdata = json.load(f)
            for user in usersdata:
                self.userlist.append(User(user))
        self._i = 0

    def __iter__(self):
        i = 0
        while i < len(self.userlist):
            yield self.userlist[i]
            i += 1

    def get_user_by_id(self, id) -> Union[User, None]:
        for user in self.userlist:
            if user.id == id:
                return user
        else:
            return None

    def get_display_name_by_id(self, id) -> str:
        for user in self.userlist:
            if user.id == id:
                return user.display_name
        else:
            return ""


class MsgFile:
    def __init__(
        self,
        id: str,
        timestamp: int,
        name: str,
        mimetype: str,
        filetype: str,
        url: str,
        filesdirpath: Union[os.PathLike, str],
    ) -> None:
        self.id = id
        self.timestamp = timestamp
        self.name = name
        self.mimetype = mimetype
        self.filetype = filetype
        self.url = url
        self.filepath = Path(filesdirpath).joinpath(self.id)
        self.downloadfile()

    def downloadfile(self) -> None:
        util.downloadfile(self.url, self.filepath)

    def to_discord_file(self) -> discord.File:
        return discord.File(self.filepath, filename=self.name)


class MsgAttachment:
    def __init__(self, title: str, text: str, url: str) -> None:
        self.title = title
        self.text = text
        self.url = url

    def to_text(self) -> str:
        text = self.text
        if self.url:
            text = f"{self.url}\n{text}"
        if self.title:
            text = f"**{self.title}**\n{text}"
        if self.text:
            text = re.sub(r"^", r"> ", text)
            text = re.sub(r"\n", r"\n> ", text)
        return text


class Message:
    def __init__(
        self,
        type: str = "",
        user_id: str = "",
        user_name: str = "",
        ts: str = "",
        text: str = "",
        files: List[MsgFile] = [],
        attachments: List[MsgAttachment] = [],
        thread_ts: str = "",
        has_thread: bool = False,
        is_reply: bool = False,
        reply_count: int = 0,
        replies_ts: List[str] = [],
    ) -> None:
        self.type = type
        self.user_id = user_id
        self.user_name = user_name
        self.ts = ts
        self.date = util.ts2date(ts)
        self.text = text
        self.files = files
        self.attachments = attachments
        self.thread_ts = thread_ts
        self.has_thread = has_thread
        self.is_reply = is_reply
        self.reply_count = reply_count
        self.replies_ts = replies_ts

    def to_text(self) -> str:
        text = f"**{self.user_name}** *({self.date})*\n{self.text}"
        for attachment in self.attachments:
            text += "\n" + attachment.to_text()
        return text

    def get_discord_files(self) -> List[discord.File]:
        discord_files: List[discord.File] = []
        for file in self.files:
            discord_files.append(file.to_discord_file())
        return discord_files


class Messages:
    def __init__(self) -> None:
        self.messagelist: List[Message] = []

    def __iter__(self):
        i = 0
        while i < len(self.messagelist):
            yield self.messagelist[i]
            i += 1

    def add_message(self, message: Message) -> None:
        self.messagelist.append(message)

    def find_message_by_ts(self, ts: str) -> Union[Message, None]:
        for message in self.messagelist:
            if message.ts == ts:
                return message
        else:
            return None

    def find_replies_by_ts(self, thread_ts: str) -> List[Message]:
        replies: List[Message] = []
        for message in self.messagelist:
            if message.thread_ts == thread_ts and message.is_reply:
                replies.append(message)
        return replies

    def find_replies_by_message(self, root_message: Message) -> List[Message]:
        replies: List[Message] = []

        if not root_message.has_thread:
            return replies

        for message in self.messagelist:
            if message.thread_ts == root_message.thread_ts and message.is_reply:
                replies.append(message)
        return replies


class Channel:
    def __init__(self, channelinfo: dict, users: Users) -> None:
        self.id = channelinfo["id"]
        self.name = channelinfo["name"]
        self.topic = channelinfo["topic"]["value"]
        self.purpose = channelinfo["purpose"]["value"]
        self.members: List[User] = []
        if "members" in channelinfo:
            for userid in channelinfo["members"]:
                self.members.append(users.get_user_by_id(userid))
        self.messages: Messages = Messages()

    def add_message(self, message: Message):
        self.messages.add_message(message)


class Channels:
    def __init__(self, channelsjsonpath: Union[os.PathLike, str], users: Users) -> None:
        self.channellist: List[Channel] = []
        with open(channelsjsonpath) as f:
            channelsdata = json.load(f)
            for channel in channelsdata:
                self.channellist.append(Channel(channel, users))

    def __iter__(self):
        i = 0
        while i < len(self.channellist):
            yield self.channellist[i]
            i += 1

    def get_channel_by_id(self, id: str) -> Channel:
        for channel in self.channellist:
            if channel.id == id:
                return channel

    def get_name_by_id(self, id) -> str:
        return self.get_channel_by_id(id).name

    def channel_names(self) -> List[str]:
        return [ch.name for ch in self.channellist]
