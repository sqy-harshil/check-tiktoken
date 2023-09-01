from typing import NamedTuple


class AnalysisJSON(NamedTuple):
    json_object: dict
    token_usage: dict
    script: str
