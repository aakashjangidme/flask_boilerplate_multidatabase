import os
from dotenv import load_dotenv

load_dotenv(override=True)


class ConfigException(ValueError):
    pass


base_dir = os.path.dirname(os.path.abspath(__file__))


class Config:
    APP_NAME = "playground-x"
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    FLASK_DEBUG = False
    LOG_DIR = os.path.join(base_dir, "logs")
    LOG_FILE = f"{LOG_DIR}/{APP_NAME}.log"
    LOG_FILE_ERROR = f"{LOG_DIR}/{APP_NAME}_error.log"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")

    POSTGRES_DB_TYPE = os.getenv("POSTGRES_DB_TYPE", "postgres")
    POSTGRES_DB_USER = os.getenv("POSTGRES_DB_USER")
    POSTGRES_DB_PASSWORD = os.getenv("POSTGRES_DB_PASSWORD")
    POSTGRES_DB_HOST = os.getenv("POSTGRES_DB_HOST")
    POSTGRES_DB_PORT = os.getenv("POSTGRES_DB_PORT")
    POSTGRES_DB_NAME = os.getenv("POSTGRES_DB_NAME")

    ORACLE_DB_TYPE = os.getenv("ORACLE_DB_TYPE", "postgres")
    ORACLE_DB_USER = os.getenv("ORACLE_DB_USER")
    ORACLE_DB_PASSWORD = os.getenv("ORACLE_DB_PASSWORD")
    ORACLE_DB_HOST = os.getenv("ORACLE_DB_HOST")
    ORACLE_DB_PORT = os.getenv("ORACLE_DB_PORT")
    ORACLE_DB_NAME = os.getenv("ORACLE_DB_NAME")

    @classmethod
    def raise_config_exception_if_empty(cls):
        if not all(
            getattr(cls, attr)
            for attr in [
                "POSTGRES_DB_TYPE",
                "POSTGRES_DB_USER",
                "POSTGRES_DB_PASSWORD",
                "POSTGRES_DB_HOST",
                "POSTGRES_DB_PORT",
                "POSTGRES_DB_NAME",
            ]
        ):
            raise ConfigException("One or more configuration settings are empty.")

    @classmethod
    def create_dir(cls):
        os.makedirs(cls.LOG_DIR, exist_ok=True)

    def __init__(self):
        self.raise_config_exception_if_empty()
        self.create_dir()


class DevelopmentConfig(Config):
    FLASK_DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(Config):
    FLASK_DEBUG = False
    FLASK_ENV = "production"


config = {"development": DevelopmentConfig(), "production": ProductionConfig()}
