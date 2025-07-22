import os
import asyncio
import requests
from urllib.parse import unquote

from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.functions.users import GetUsers
from pyrogram.raw.types import InputBotAppShortName, InputUser

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
client = Client('main', api_id=api_id, api_hash=api_hash)
API_URL = 'https://portals-market.com/api'


async def get_auth_token(client: Client):
    async with client:
        peer = await client.resolve_peer("portals")
        user_full = await client.invoke(GetUsers(id=[peer]))

        bot_raw = user_full[0]
        bot = InputUser(user_id=bot_raw.id, access_hash=bot_raw.access_hash)
        bot_app = InputBotAppShortName(bot_id=bot, short_name="market")

        web_view = await client.invoke(
            RequestAppWebView(
                peer=peer,
                app=bot_app,
                platform="desktop",
            )
        )
        web_app_data = web_view.url.split('tgWebAppData=', 1)[1]
        init_data = unquote(web_app_data.split('&tgWebAppVersion', 1)[0])

        return f"tma {init_data}"


async def main():
    token = await get_auth_token(client)
    headers = {'Authorization': token}

    try:
        response = requests.get(
            f'{API_URL}/nfts/search?offset=0&limit=100',
            headers=headers)
        response_json = response.json()
        gifts = response_json['results']
        print(gifts)
    except Exception as error:
        print(error)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
