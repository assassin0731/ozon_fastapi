from sqlalchemy import Table, Column, Integer, String, TIMESTAMP, MetaData

metadata = MetaData()

price = Table(
    "price",
    metadata,
    Column("article", String, primary_key=True),
    Column("price", String),
    Column("date", TIMESTAMP),
)