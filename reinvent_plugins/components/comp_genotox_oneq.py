from __future__ import annotations

from dataclasses import dataclass

from .add_tag import add_tag
from .base_oneq import BaseOneq

__all__ = ["Toxoneq"]


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
class Toxoneq(BaseOneq):

    def __init__(self, params: Parameters):
        super().__init__()
        self.executables = params
        self.args = params
        self.tasks = []
        self.field = 'is_genotoxic'
        self.pipeline = "genotoxic"
        self.classification = True
