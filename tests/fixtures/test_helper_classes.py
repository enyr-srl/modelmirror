"""
FastAPI test classes.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from pydantic import BaseModel, ConfigDict


class MSSQLConnectionParameters:
    def __init__(
        self,
        driver: str,
        server: str,
        database: str,
        encrypt: str,
        uid: str,
        pwd: str,
        trust_server_certificate: str = "No",
    ) -> None:
        self.__driver = driver
        self.__server = server
        self.__database = database
        self.__encrypt = encrypt
        self.__uid = uid
        self.__pwd = pwd
        self.__trust_server_certificate = trust_server_certificate

    def get_connection(self) -> str:
        return (
            "DRIVER={" + self.__driver + "};" + "SERVER=" + self.__server + ";" + "DATABASE=" + self.__database + ";"
            "ENCRYPT=" + self.__encrypt + ";" + "UID=" + self.__uid + ";"
            "PWD=" + self.__pwd + ";"
            "TrustServerCertificate=" + self.__trust_server_certificate + ";"
        )

    def get_database_ref(self) -> str:
        return f"mssql://{self.__server}/{self.__database}"


class LanguageStore(ABC):
    @abstractmethod
    async def get_language_codes(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def get_language_translations(self, language_code: str) -> Dict[str, str]:
        raise NotImplementedError


class MSSQLConnectionPool:
    def __init__(self, connection_parameters: MSSQLConnectionParameters) -> None:
        self.__connection_parameters = connection_parameters


class MssqlLanguageStore(LanguageStore):
    def __init__(self, connection_pool: MSSQLConnectionPool, translations_table: str) -> None:
        self.__connection_pool = connection_pool

    async def get_language_codes(self) -> List[str]:
        return []

    async def get_language_translations(self, language_code: str) -> Dict[str, str]:
        return {}


class Language:
    def __init__(self, store: LanguageStore, locales_dir: str) -> None:
        self.__store = store
        self.__locales_dir = locales_dir

    def __call__(self):
        print("Language called")


class International(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
    language: Language


class AppModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
    dataSourcesParams: list[MSSQLConnectionParameters]
    international: International
