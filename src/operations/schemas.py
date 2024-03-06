from datetime import datetime

from pydantic import BaseModel


class Price(BaseModel):
    article: str
    price: str
    date: datetime


class Order(BaseModel):
    id: str
    article: str
    quantity: int
    price: str | None
    total: str | None
    earnings: str | None
    order_date: datetime
    arrive_date: datetime | None
