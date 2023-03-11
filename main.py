import asyncio
import datetime
import json
import logging
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
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
        async with async_session() as session:
            try:
                await run_tracking(session)
            except ConnectionClosedError as error:
                log.error(f'Connection error: {error}')


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

            # check_price_change()

            print(
                price_info.btc_trade_time,
                price_info.btc_price,
                '\n',
                price_info.eth_trade_time,
                price_info.eth_price
            )

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
