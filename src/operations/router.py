from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from operations.models import price

router = APIRouter(
    prefix="/prices",
    tags=["Prices"]
)


@router.get("/")
async def get_prices(session: AsyncSession = Depends(get_async_session)):
    query = select(price)
    result = await session.execute(query)
    return result.mappings().all()