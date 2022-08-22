# slack2discord

The tool to migrate from slack to discord.

# Usage

## Create Discord Bot

See https://guide.pycord.dev/getting-started/creating-your-first-bot .

This script the following permissions:

- Manage Channels
- Read Messages/View Channels
- Send Messages
- Create Public Threads
- Send Messages in Threads
- Embed Links
- Attach Files
- Mension Everyone
- Use Slash Commands

## Export Slack Workspace Data

See https://slack.com/help/articles/201658943-Export-your-workspace-data .


## Migrate Slack to Discord

1. Clone this repository.
   ```
   git clone https://github.com/yano404/slack2discord.git
   ```
2. Install requirements.
   ```
   poetry install
   ```
3. Edit `.env` .
   ```
   EXPORTED_DATA_DIR = "data/exported_json/<your slack workspace data>"
    FILES_DIR = "data/files"
    TOKEN = "YOUR DISCORD BOT TOKEN"
   ```
4. Run `s2d.py`.
   ```
   poetry run python s2d.py
   ```
5. Type `/restore` in the discord channel.
# License

Copyright (c) 2022 Takayuki YANO

The source code is licensed under the MIT License, see LICENSE.