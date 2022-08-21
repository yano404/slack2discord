import json
import os
import re
import sys
from html import unescape
from pathlib import Path
from typing import List, Union

from tqdm import tqdm

from . import model, util


class SlackData:
    def __init__(
        self, datadir: Union[os.PathLike, str], filesdirpath: Union[os.PathLike, str]
    ) -> None:
        self.datadir: Path = Path(datadir)
        self.channelsjsonpath = datadir.joinpath("channels.json")
        self.usersjsonpath = datadir.joinpath("users.json")
        try:
            self.users = model.Users(self.usersjsonpath)
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)
        try:
            self.channels = model.Channels(self.channelsjsonpath, self.users)
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)
        self.filesdirpath: Path = Path(filesdirpath)

    def parse_all_messages(self):
        for ch in self.channels:
            self.parse_messages_in_channel(ch.id)

    def parse_messages_in_channel(self, channelid: str):
        ch = self.channels.get_channel_by_id(channelid)

        print(f"Processing #{ch.name}")

        chpath = self.datadir.joinpath(ch.name)
        jsonpaths = sorted(
            [
                p
                for p in chpath.glob("*.json")
                if re.search(r"\d{4}-\d{2}-\d{2}.json", str(p))
            ]
        )
        bar = tqdm(total=len(jsonpaths))
        for jsonpath in jsonpaths:
            with open(jsonpath) as f:
                rawmsgs = json.load(f)
                for rawmsg in rawmsgs:
                    ch.add_message(self.parse_message(rawmsg))
            bar.update(1)

    def parse_message(self, rawmsg: dict) -> model.Message:
        type: str = ""
        user_id: str = ""
        user_name: str = ""
        ts: str = ""
        text: str = ""
        files: List[model.MsgFile] = []
        attachments: List[model.MsgAttachment] = []
        thread_ts: str = ""
        has_thread: bool = False
        is_reply: bool = False
        reply_count: int = 0
        replies_ts: List[str] = []

        type = rawmsg["type"]

        if "user" in rawmsg:
            user_id = rawmsg["user"]
        elif "bot_id" in rawmsg:
            user_id = rawmsg["bot_id"]

        user_name = self.users.get_display_name_by_id(user_id)

        ts = rawmsg["ts"]

        text = rawmsg["text"]
        text = self.fill_references(text)
        text = unescape(text)
        text = util.replace(text)

        if "files" in rawmsg:
            for fileinfo in rawmsg["files"]:
                if fileinfo["mode"] == "hosted":
                    file_id: str = fileinfo["id"]
                    file_timestamp: int = fileinfo["timestamp"]
                    file_name: str = fileinfo["name"]
                    file_mimetype: str = util.url_unescape(fileinfo["mimetype"])
                    file_filetype: str = fileinfo["filetype"]
                    file_url: str = util.url_unescape(fileinfo["url_private_download"])
                    files.append(
                        model.MsgFile(
                            id=file_id,
                            timestamp=file_timestamp,
                            name=file_name,
                            mimetype=file_mimetype,
                            filetype=file_filetype,
                            url=file_url,
                            filesdirpath=self.filesdirpath,
                        )
                    )

        if "attachments" in rawmsg:
            for attachmentinfo in rawmsg["attachments"]:
                attachment_title: str = (
                    attachmentinfo["title"] if "title" in attachmentinfo else ""
                )
                attachment_text: str = util.modify_googlecal_date(
                    attachmentinfo["text"] if "texte" in attachmentinfo else ""
                )
                attachment_text = self.fill_references(attachment_text)
                attachment_text = unescape(attachment_text)
                attachment_url: str = util.url_unescape(
                    attachmentinfo["original_url"]
                    if "original_url" in attachmentinfo
                    else ""
                )
                attachments.append(
                    model.MsgAttachment(
                        title=attachment_title, text=attachment_text, url=attachment_url
                    )
                )

        if "thread_ts" in rawmsg:
            thread_ts = rawmsg["thread_ts"]

        if "reply_count" in rawmsg:
            reply_count = rawmsg["reply_count"]
            has_thread = True
            for replyinfo in rawmsg["replies"]:
                replies_ts.append(replyinfo["ts"])

        if "parent_user_id" in rawmsg:
            is_reply = True

        return model.Message(
            type=type,
            user_id=user_id,
            user_name=user_name,
            ts=ts,
            text=text,
            files=files,
            attachments=attachments,
            thread_ts=thread_ts,
            has_thread=has_thread,
            is_reply=is_reply,
            reply_count=reply_count,
            replies_ts=replies_ts,
        )

    def fill_references(self, text: str):
        for user in self.users.userlist:
            text = text.replace(f"<@{user.id}>", f"@{user.display_name}")
        for channel in self.channels.channellist:
            text = text.replace(f"<#{channel.id}>", f"#{channel.name}")
        return text
