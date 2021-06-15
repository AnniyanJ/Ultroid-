# Ultroid - UserBot
# Copyright (C) 2021 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

"""
✘ Commands Available -

"""

import os

import requests
from ProfanityDetector import detector

from . import *


@ultroid_cmd(pattern="addprofanity$", admins_only=True)
async def addp(e):
    profan_chat(e.chat_id, action)
    await eor(e, "Added This Chat To Profanity Filter")


@ultroid_cmd(pattern="remprofanity", admins_only=True)
async def remp(e):
    rem_profan(e.chat_id)
    await eor(e, "Removed This Chat from Profanity Filter.")

@ultroid_bot.on(events.NewMessage(incoming=True))
async def checkprofan(e):
    chat = e.chat_id
    if is_profan(chat) and e.text:
        x, y = detector(e.text)
        if y:
            await e.delete()
