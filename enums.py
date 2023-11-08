from enum import Enum


class HttpStatusCode(Enum):
    OK: int = 200
    BAD_REQUEST: int = 400
    UNAUTHORIZED: int = 401
    NOT_FOUND: int = 404
    INTERNAL_SERVER_ERROR: int = 500
