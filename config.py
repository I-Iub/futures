import datetime
import logging
import os

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, PostgresDsn

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_level_variable = os.getenv('LOGGING_LEVEL', logging.INFO).upper()
log_level = getattr(logging, log_level_variable)
window = datetime.timedelta(seconds=int(os.getenv('WINDOW', 10)))


class Settings(BaseSettings):
    dsn: PostgresDsn
    interval: int = Field(60, env='INTERVAL')
    log_level: int = log_level
    ping_timeout: int = Field(20, env='PING_TIMEOUT')
    thresholding: float = Field(1.0, env='THRESHOLDING')
    uri: str = Field('wss://stream.binancefuture.com/ws/', env='URI')
    window: datetime.timedelta = window

    class Config:
        env_file = BASE_DIR + '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
