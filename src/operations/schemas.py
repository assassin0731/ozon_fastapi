from datetime import datetime

from pydantic import BaseModel


class Price(BaseModel):
    article: str
    price: str
    date: datetime
