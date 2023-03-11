from datetime import datetime
from pydantic import BaseModel


class PriceInfo(BaseModel):
    btc_trade_time: datetime
    btc_price: float
    eth_trade_time: datetime
    eth_price: float
