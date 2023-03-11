import os

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, PostgresDsn

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Settings(BaseSettings):
    dsn: PostgresDsn
    ping_timeout = Field(20, env='PING_TIMEOUT')
    uri = Field('wss://stream.binancefuture.com/ws/', env='URI')

    class Config:
        env_file = BASE_DIR + '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
