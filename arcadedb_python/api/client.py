from . import config
from abc import ABC, abstractmethod

import logging
import requests

from retry import retry
from ..exceptions import LoginFailedException, ConnectionException


class Client(ABC):
    def __init__(self, host: str, port: str, protocol: str = "http", **kwargs):
        self.host = host
        self.port = int(port)
        self.kwargs = kwargs
        self.protocol = protocol
        self._validate()

    def _validate(self):
        if not self.host:
            raise ValueError("Host is required")
        if not self.port:
            raise ValueError("Port is required")
        endpoint_test = config.ARCADE_BASE_SERVER_ENDPOINT
        try:
            self.post(endpoint_test,  { "command": "list databases" })
            
        except LoginFailedException as e:
            if e.java_error_code == "com.arcadedb.server.security.ServerSecurityException":
                raise ConnectionException("Invalid credentials", java_error_code=e.java_error_code, detail=e.detail)
            else:
                raise ConnectionException("Unable to connect to server", java_error_code=e.java_error_code, detail=str(e))
        except Exception as e:
            raise ConnectionException("Unable to connect to server", detail=str(e))
        
        


    def _get_endpoint(self, endpoint: str) -> str:
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        if self.url.endswith("/"):
            return f"{self.url}{endpoint}"
        else:
            return f"{self.url}/{endpoint}"

    @property
    def headers(self):
        default = "application/json"
        key = "content_type"
        if key not in self.kwargs:
            logging.warning(f"No content type, defaulting to {default}")
        content_type = self.kwargs.get(key, default)
        return {"Content-Type": content_type}

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def username(self) -> str:
        return self.kwargs.get("username") or self.kwargs.get("user")

    @property
    def password(self) -> str:
        return self.kwargs.get("password") or self.kwargs.get("pw")

    def __repr__(self) -> str:
        return f"<host={self.host} port={self.port} user={self.username}>"

    def __str__(self) -> str:
        return self.__repr__()
    
   
        


    @abstractmethod
    @retry(
        tries=config.API_RETRY_MAX,
        delay=config.API_RETRY_DELAY,
        backoff=config.API_RETRY_BACKOFF,
    )
    def post(self, endpoint: str, payload: dict, return_headers: bool=False, extra_headers: dict = {}) -> requests.Response:
        pass

    @abstractmethod
    @retry(
        tries=config.API_RETRY_MAX,
        delay=config.API_RETRY_DELAY,
        backoff=config.API_RETRY_BACKOFF,
    )
    def get(self, endpoint: str, return_headers: bool=False, extra_headers: dict = {}) -> requests.Response:
        pass

    
