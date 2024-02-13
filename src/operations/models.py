from sqlalchemy import Table, Column, Integer, String, TIMESTAMP, MetaData, Float

metadata = MetaData()

price = Table(
    "price",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("article", String),
    Column("price", Float),
    Column("date", TIMESTAMP),
)