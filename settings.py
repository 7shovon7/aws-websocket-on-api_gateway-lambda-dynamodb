import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
    WS_ENDPOINT = os.getenv("WS_ENDPOINT")
    DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")


settings = Settings()
