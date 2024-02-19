import datetime

import requests
from fastapi import APIRouter

from funcs import orders, headers

order = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@order.get("/")
def get_today_orders():
    get_url = "https://api-seller.ozon.ru/v3/posting/fbs/list"
    json_data = orders
    now = datetime.date.today()
    json_data["filter"]["since"] = f"{now -datetime.timedelta(days=1)}T02:00:00.000Z"
    json_data["filter"]["to"] = f"{now}T02:00:00.000Z"
    today_orders = requests.post(get_url, headers=headers, json=json_data).json()
    return {'status': 200, 'data': today_orders}
