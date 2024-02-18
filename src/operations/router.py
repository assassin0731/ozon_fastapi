import datetime

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi_users.schemas import model_dump
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from funcs import upload_excel, stock_dict
from operations.models import price
from operations.schemas import Price

router = APIRouter(
    prefix="/prices",
    tags=["Prices"]
)


@router.get("/")
async def get_prices(session: AsyncSession = Depends(get_async_session)):
    query = select(price)
    result = await session.execute(query)
    return result.mappings().all()


@router.post("/")
async def upload_prices(file: UploadFile = File(...), session: AsyncSession = Depends(get_async_session)):
    contents = await file.read()
    stock = upload_excel(file, contents)
    query = select(price.c.article)
    result = await session.execute(query)
    articles = {art['article'] for art in result.mappings().all()}
    for i, item in enumerate(stock.items(), 1):
        art, cur_price = item[0], item[1][1]
        cur_price = Price(article=art, price=cur_price, date=datetime.datetime.now())
        if art not in articles:
            stmt = insert(price).values(model_dump(cur_price))
        else:
            stmt = update(price).where(price.c.article == art).values(model_dump(cur_price))
        await session.execute(stmt)
    await session.commit()
    return {"status": "success"}