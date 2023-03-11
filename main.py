import asyncio
import datetime
import json
import logging
import time
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import and_, func, select
from sqlalchemy.exc import ProgrammingError
from websockets import connect
from websockets.exceptions import ConnectionClosedError

import logger
from db.database import async_session
from db.models import Price
from config import settings
from models import PriceInfo

log = logging.getLogger()


async def main() -> None:
    while True:
        try:
            async with async_session() as session:
                try:
                    await run_tracking(session)
                except ConnectionClosedError as error:
                    log.error(f'Connection error: {error}')
        except ProgrammingError:
            log.error('Please, check that migrations are applied')
            time.sleep(10)


async def run_tracking(session: AsyncSession) -> None:
    async with (
        connect(settings.uri + 'btcusdt@aggTrade',
                ping_timeout=settings.ping_timeout) as btc_stream,
        connect(settings.uri + 'ethusdt@aggTrade',
                ping_timeout=settings.ping_timeout) as eth_stream
    ):
        while True:
            responses = await asyncio.gather(btc_stream.recv(),
                                             eth_stream.recv())
            price_info = get_price_info(responses)
            log.debug('BTCUSDT: price=%s, trade_time=%s '
                      'ETHUSDT: price=%s trade_time=%s',
                      price_info.btc_price, price_info.btc_trade_time,
                      price_info.eth_price, price_info.eth_trade_time)
            await check_price_change(session, price_info)
            await write_to_database(session, price_info)


def get_price_info(responses: Iterable[str]) -> PriceInfo:
    btc_response, eth_response = [
        json.loads(response) for response in responses
    ]
    btc_trade_time = datetime.datetime.fromtimestamp(
        btc_response.get('T') / 1000
    )
    eth_trade_time = datetime.datetime.fromtimestamp(
        eth_response.get('T') / 1000
    )
    btc_price = float(btc_response.get('p'))
    eth_price = float(eth_response.get('p'))
    return PriceInfo(btc_trade_time=btc_trade_time,
                     eth_trade_time=eth_trade_time,
                     btc_price=btc_price,
                     eth_price=eth_price)


async def check_price_change(
        session: AsyncSession, price_info: PriceInfo
) -> None:
    previous_time = (
        datetime.datetime.now() - datetime.timedelta(minutes=settings.interval)
    )
    # Для того чтобы сгладить "выбросы" цены делаем выборку средних значений
    # за небольшой промежуток времени settings.window (см. WINDOW в файле
    # ".env")
    statement = (
        select(func.avg(Price.btc_price), func.avg(Price.eth_price))
        .where(and_(Price.btc_trade_time >= previous_time - settings.window,
                    Price.btc_trade_time <= previous_time,
                    Price.eth_trade_time >= previous_time - settings.window,
                    Price.eth_trade_time <= previous_time))
    )
    result = await session.execute(statement)
    btc_price_prev, eth_price_prev = result.first()
    if btc_price_prev is None or eth_price_prev is None:
        return
    btc_change = (price_info.btc_price - btc_price_prev) / btc_price_prev * 100
    eth_change = (price_info.eth_price - eth_price_prev) / eth_price_prev * 100
    eth_self_change = eth_change - btc_change

    if abs(eth_self_change) >= settings.thresholding:
        rounded_change = round(eth_self_change, 3)
        log.info('The price change (%s) has exceeded the threshold',
                 rounded_change)


async def write_to_database(session: AsyncSession, record: PriceInfo) -> None:
    record = Price(**record.dict())
    session.add(record)
    await session.commit()


if __name__ == '__main__':
    logger.configure_logger()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info('User interrupted program.')
