from sqlalchemy import Table, Column, Integer, String, TIMESTAMP, MetaData

metadata = MetaData()

price = Table(
    "price",
    metadata,
    Column("article", String, primary_key=True),
    Column("price", String),
    Column("date", TIMESTAMP),
)


order_table = Table(
    "order",
    metadata,
    Column("id", String, nullable=False),
    Column("article", String, nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("price", String),
    Column("total", String),
    Column("earnings", String),
    Column("order_date", TIMESTAMP, nullable=False),
    Column("arrive_date", TIMESTAMP)
)