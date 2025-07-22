import os
import asyncio
import requests
from urllib.parse import unquote
from datetime import datetime
from math import floor

from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.functions.users import GetUsers
from pyrogram.raw.types import InputBotAppShortName, InputUser

from typing import List, Optional
from pydantic import BaseModel, HttpUrl, TypeAdapter


class CollectionPreview(BaseModel):
    name: str
    url: HttpUrl


class Collection(BaseModel):
    id: str
    name: str
    short_name: str
    preview: CollectionPreview


class TopOrderCollection(BaseModel):
    name: str
    photo_url: HttpUrl
    short_name: str
    floor_price: float


class TopOrder(BaseModel):
    id: str
    collection_id: str
    amount: float
    max_nfts: int
    current_nfts: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    collection: TopOrderCollection


collections_adapter = TypeAdapter(List[Collection])
top_order_adapter = TypeAdapter(TopOrder)


api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
client = Client('main', api_id=api_id, api_hash=api_hash)
API_URL = 'https://portals-market.com/api'


async def get_auth_token(client: Client) -> str:
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


def get_collections(token: str) -> List[Collection]:
    url = f'{API_URL}/collections/filters/preview?owned_only=false'
    headers = {'Authorization': token}

    try:
        response = requests.get(url, headers=headers)
        response_json = response.json()
        collections = response_json['collections']

        return collections_adapter.validate_python(collections)
    except Exception as error:
        print(error)


def get_collection_top_order(collection_id: str, token: str)\
        -> TopOrder | None:
    url = f'{API_URL}/collection-offers/{collection_id}/top'
    headers = {'Authorization': token}

    try:
        response = requests.get(url, headers=headers)
        response_json = response.json()

        if len(response_json):
            order = response_json[0]
            return top_order_adapter.validate_python(order)

    except Exception as error:
        print(error)


async def main():
    token = await get_auth_token(client)
    collections = get_collections(token)

    for collection in collections:
        order = get_collection_top_order(collection.id, token)
        if not order:
            continue

        order_price = floor((order.amount * 0.95) * 100) / 100
        price_difference = order_price - order.collection.floor_price

        if price_difference >= 0.1:
            print(
                f'''
                    🏷️{collection.name}
                    💲Order price: {order_price}
                    💰Floor price: {order.collection.floor_price}
                    💸Profit: {price_difference}
                ''')

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
