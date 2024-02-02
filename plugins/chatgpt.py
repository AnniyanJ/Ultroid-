# Written by @TrueSaiyan Credits to dot arc for OpenAI
# Ultroid ~ UserBot
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid >
# PLease read the GNU Affero General Public License in
# <https://github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.
"""
**Get Answers from Chat GPT including OpenAI, Bing and Sydney**
**Or generate images with Dall-E-3XL**

> `{i}gpt` (-i = for image) (query)

**• Examples: **
> `{i}gpt How to fetch a url in javascript`
> `{i}gpt -i Cute Panda eating bamboo`
> `{i}bard Hello world`
> `{i}igen Cute Panda eating bamboo`

• `{i}gpt` or `{i}gpt -i` Needs OpenAI API key to function!!
• `{i}igen` Dall-E-3-XL
• `{i}bard` Need to save bard cookie to use bard. (Its still learning)
"""
import aiohttp
import asyncio
from os import remove, system
from telethon import TelegramClient, events
from io import BytesIO
from PIL import Image
import base64
import requests
import json
from pyUltroid.fns.tools import AwesomeCoding
from . import *


try:
    import openai
    from bardapi import Bard
except ImportError:
    system("pip3 install -q openai")
    system("pip3 install -q bardapi")
    import openai
    from bardapi import Bard

from . import (
    LOGS,
    async_searcher,
    check_filename,
    fast_download,
    udB,
    ultroid_cmd,
)

if udB.get_key("UFOPAPI"):
    UFoPAPI = udB.get_key("UFOPAPI")
else:
    UFoPAPI = ""

if udB.get_key("BARDAPI"):
    BARD_TOKEN = udB.get_key("BARDAPI")
else:
    BARD_TOKEN = None
    

#------------------------------ GPT v1 ------------------------------#
# OpenAI API-Key Required                                            |
#--------------------------------------------------------------------#
@ultroid_cmd(
    pattern="(chat)?gpt( ([\\s\\S]*)|$)",
)
async def openai_chat_gpt(e):
    api_key = udB.get_key("OPENAI_API")
    if not api_key:
        return await e.eor("OPENAI_API key missing..")

    args = e.pattern_match.group(3)
    reply = await e.get_reply_message()
    if not args:
        if reply and reply.text:
            args = reply.message
    if not args:
        return await e.eor("Gimme a Question to ask from ChatGPT")

    eris = await e.eor("Getting response...")
    gen_image = False
    if not OPENAI_CLIENT:
        OPENAI_CLIENT = openai.AsyncOpenAI(api_key=api_key)
    if args.startswith("-i"):
        gen_image = True
        args = args[2:]

    if gen_image:
        try:
            response = await OPENAI_CLIENT.images.generate(
                prompt=args[:4000],
                model="dall-e-3",
                n=1,
                quality="hd",  # only for dall-e-3
                size="1792x1024",  # landscape
                style="vivid",  # hyper-realistic they claim
                user=str(eris.client.uid),
            )
            img_url = response.data[0].url
            path, _ = await fast_download(img_url, filename=check_filename("dall-e.png"))
            await e.respond(
                f"<i>{args[:636]}</i>",
                file=path,
                reply_to=e.reply_to_msg_id or e.id,
                parse_mode="html",
            )
            remove(path)
            await eris.delete()
        except Exception as exc:
            LOGS.warning(exc, exc_info=True)
            await eris.edit(f"GPT (v1) ran into an Error:\n\n> {exc}")

        return

    try:
        response = await OPENAI_CLIENT.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": args}],
        )
        # LOGS.debug(f'Token Used on ({question}) > {response["usage"]["total_tokens"]}')
        answer = response.choices[0].message.content.replace("GPT:\n~ ", "")

        if len(response.choices[0].message.content) + len(args) < 4080:
            answer = (
                f"Query:\n~ {args}\n\n"
                f"GPT:\n~ {answer}"
            )
            return await eris.edit(answer)

        with BytesIO(response.encode()) as file:
            file.name = "gpt_response.txt"
            await e.respond(
                f"<i>{args[:1000]} ...</i>",
                file=file,
                reply_to=e.reply_to_msg_id or e.id,
                parse_mode="html",
            )
            await eris.delete()
    except Exception as exc:
        LOGS.warning(exc, exc_info=True)
        await eris.edit(f"GPT (v1) ran into an Error:\n\n> {exc}")


#--------------------------Open Dall-E ----------------------------#
# UFoP API                                                         |
#------------------------------------------------------------------#

@ultroid_cmd(
    pattern="(chat)?igen( ([\\s\\S]*)|$)",
)
async def handle_dalle3xl(message):
    query = message.raw_text.split('.igen', 1)[-1].strip()
    reply = await message.edit(f"Generating image...")

    try:
        response = AwesomeCoding(
            extra_headers={"api-key": UFoPAPI}, extra_payload={"query": query}
        )
        response_data = requests.post(
            response.dalle3xl_url.decode("utf-16"),
            headers=response.extra_headers,
            json=response.extra_payload).json()

        if "randydev" in response_data:
            image_data_base64 = response_data["randydev"]["data"]
            image_data = base64.b64decode(image_data_base64)

            image_filename = "output.jpg"

            with open(image_filename, "wb") as image_file:
                image_file.write(image_data)

            caption = f"{query}"
            await reply.delete()
            await message.client.send_file(
                message.chat_id,
                image_filename,
                caption=caption,
                reply_to=message.reply_to_msg_id if message.is_reply and message.reply_to_msg_id else None,
            )

            os.remove(image_filename)
        else:
            LOGS.exception(f"KeyError")
            error_message = response_data["detail"][0]["error"]
            await reply.edit(error_message)
            return

    except requests.exceptions.RequestException as e:
        LOGS.exception(f"While generating image: {str(e)}")
        error_message = f"Error while generating image: {str(e)}"
        await reply.edit(error_message)

    except KeyError as e:
        LOGS.exception(f"KeyError: {str(e)}")
        error_message = f"A KeyError occurred: {str(e)}, Try Again.."
        await reply.edit(error_message)
        await asyncio.sleep(3)
        await reply.delete()

    except Exception as e:
        LOGS.exception(f"Error: {str(e)}")
        error_message = f"An unexpected error occurred: {str(e)}"
        await reply.edit(error_message)


#--------------------------Bard w Base ----------------------------#
# Bard Cookie Token.                                               |
#------------------------------------------------------------------#

@ultroid_cmd(
    pattern="(chat)?bard( ([\\s\\S]*)|$)",
)
async def handle_bard(message):
    owner_base = "You are an AI Assistant chatbot called Ultroid AI designed for many different helpful purposes"
    query = message.raw_text.split('.bard', 1)[-1].strip()
    reply = await message.edit(f"Generating answer...")

    if BARD_TOKEN:
        token = BARD_TOKEN
    else:
        error_message = f"ERROR NO BARD COOKIE TOKEN"
        await reply.edit(error_message)
        return

    try:
        headers = {
            "Host": "bard.google.com",
            "X-Same-Domain": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Origin": "https://bard.google.com",
            "Referer": "https://bard.google.com/",
        }

        cookies = {"__Secure-1PSID": token}

        async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
            bard = Bard(token=token, session=session, timeout=30)
            bard.get_answer(owner_base)["content"]
            message_content = bard.get_answer(query)["content"]
            await reply.edit(message_content)

    except Exception as e:
        LOGS.exception(f"Error: {str(e)}")
        error_message = f"An unexpected error occurred: {str(e)}"
        await reply.edit(error_message)
