
from __future__ import annotations

from dataclasses import dataclass

from .add_tag import add_tag
from .base_oneq import BaseOneq

__all__ = ["LogPoneq"]


@add_tag("__parameters")
@dataclass
class Parameters:
    """Parameters for the scoring component

    Note that all parameters are always lists because components can have
    multiple endpoints and so all the parameters from each endpoint is
    collected into a list.  This is also true in cases where there is only one
    endpoint.
    """

    #executable: List[str]
    #args: List[str]


@add_tag("__component")
class LogPoneq(BaseOneq):

    def __init__(self, params: Parameters):
        super().__init__()
        self.params = params
        self.tasks = []
        self.field = "logp"
        self.pipeline = "lipophilicity"
        self.classification = False
