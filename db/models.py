from sqlalchemy import Column, DateTime, Integer, Float

from db.database import Base


class Price(Base):
    __tablename__ = 'prices'

    id = Column(Integer, primary_key=True, unique=True, index=True)
    btc_trade_time = Column(DateTime, nullable=False, index=True)
    btc_price = Column(Float(), nullable=False)
    eth_trade_time = Column(DateTime, nullable=False, index=True)
    eth_price = Column(Float(), nullable=False)
