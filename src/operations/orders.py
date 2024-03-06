import datetime

import requests
from fastapi import APIRouter, Depends
from fastapi_users.schemas import model_dump
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from funcs import orders, headers
from operations.models import price, order_table
from operations.schemas import Order

order = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@order.get("/")
async def get_today_orders(session: AsyncSession = Depends(get_async_session)):
    query = select(price)
    result = await session.execute(query)
    result = result.mappings().all()
    prices = dict()
    for r in result:
        prices[r['article']] = r['price']
    get_url = "https://api-seller.ozon.ru/v3/posting/fbs/list"
    json_data = orders
    now = datetime.date.today()
    json_data["filter"]["since"] = f"{now -datetime.timedelta(days=1)}T02:00:00.000Z"
    json_data["filter"]["to"] = f"{now}T02:00:00.000Z"
    today_orders = requests.post(get_url, headers=headers, json=json_data).json()['result']['postings']
    new_orders = dict()
    for td in today_orders:
        new_orders[td['posting_number']] = dict()
        for good in td['products']:
            new_orders[td['posting_number']][good['offer_id']] = dict()
            new_orders[td['posting_number']][good['offer_id']]['quantity'] = good['quantity']
            if good['offer_id'] in prices:
                new_orders[td['posting_number']][good['offer_id']]['price'] = prices[good['offer_id']]
                new_orders[td['posting_number']][good['offer_id']]['total'] = \
                    str(round(float(prices[good['offer_id']]) * good['quantity'], 2))
            else:
                new_orders[td['posting_number']][good['offer_id']]['price'] = None
                new_orders[td['posting_number']][good['offer_id']]['total'] = None
    return {'status': 200, 'data': new_orders}


@order.post("/")
async def load_today_orders(session: AsyncSession = Depends(get_async_session)):
    new_orders = await get_today_orders(session)
    for no in new_orders['data'].keys():
        for art, vals in new_orders['data'][no].items():
            cur_order = Order(id=no, article=art, quantity=vals['quantity'], price=vals['price'], total=vals['total'],
                              order_date=datetime.datetime.now(), earnings=None, arrive_date=None)
            stmt = insert(order_table).values(model_dump(cur_order))
            await session.execute(stmt)
    await session.commit()
    return {"status": "success"}