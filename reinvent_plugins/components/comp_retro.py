from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import List, Optional, Union, Dict

import numpy as np
from loguru import logger
from requests import get, post
from tqdm import tqdm

from .add_tag import add_tag
from .component_results import ComponentResults

__all__ = ["Retro"]


class Status(Enum):
    UNKNOWN = 0
    WAIT = 1
    OK = 2
    ERROR = 3


@add_tag("__parameters")
@dataclass
class Parameters:
    bearer: List[str]


@add_tag("__component")
class Retro:

    def __init__(self, params: Parameters):
        self.params = params
        if self.params.bearer:
            self.bearer = self.params.bearer
        elif bearer := os.getenv("BEARER"):
            self.bearer = bearer
        else:
            raise ValueError("Bearer value should be provided")
        self.headers = {"Authorization": self.bearer}
        self.tasks = []
        self.field = ""

    def __call__(self, smilies: List[str]) -> np.array:
        logger.info(f"module retrosynthesis setting tasks")
        scores = []
        tasks = []
        for smi in tqdm(smilies):
            logger.debug(f"smi{smi}")
            if history := self.search(smi=smi):
                task_id = history['items'][0]['id']
            else:
                task_id = self.set_task(smi)
            logger.debug(f"smi{smi}, taskid {task_id}")
            tasks.append(task_id)
        res = []
        logger.info(f"module {self.pipeline} getting tasks")
        for task in tqdm(tasks):
            res.append(self.get_task(task_id=task))
        scores.append(np.array(res))

        return ComponentResults(scores)

    def set_task(self, smi):
        # set task
        data = {
                  "name": "Reinvent",
                  "smiles": [
                    smi
                  ],
                  "mde_id": 0,
                  "max_stages": 0,
                  "max_search_time": 0,
                  "policy": "uspto",
                  "stocks": ["chemsoft", "bld", "chemconsult", "angene"],
                  "is_screening": False
                }
        for _ in range(5):
            response = post(f"https://chemlab-back.dev.net.biocad.ru/v1/retrosynth/calc/",
                            headers=self.headers, json=data)
            logger.debug(response)
            logger.debug(response.text)
            if response.status_code == 200:
                break
            sleep(10)
        task_id = response.json()["id"]
        return task_id

    def status_ok(self, task_id):
        response = json.loads(get(f"https://chemlab-back.dev.net.biocad.ru/v1/retrosynth/calc/{task_id}/",
                              headers=self.headers).text)
        status = int(response['status'])
        return Status(status)

    def get_task(self, task_id, sleep_time=10, give_up_time=3600) -> Union[np.float, np.nan, np.int]:
        # get results
        for _ in range(give_up_time // sleep_time):
            if self.status_ok(task_id=task_id) == Status.OK:
                result = get(f"https://chemlab-back.dev.net.biocad.ru/v1/retrosynth/calc/{task_id}/",
                             headers=self.headers).json()
                res = result['calcs'][0]['statistics']['is_molecule_solved']
                return np.int(res)
            logger.debug(f"task {task_id} is not ready, waiting {sleep_time} sec")
            sleep(sleep_time)
        return np.nan

    def search(self, smi: Optional[str] = None, mde_id: Optional[int] = None, user_id: Optional[str] = None,
               offset: Optional[int] = None) -> Optional[Dict]:
        # get results
        data = {"smiles": smi, "mde_id": mde_id, "user": user_id, "offset": offset}
        response = get(f"https://chemlab-back.dev.net.biocad.ru/v1/retrosynth/calc/history/",
                       headers=self.headers, params=data)
        if response.status_code == 200:
            result = response.json()
            logger.debug(result)
            if result.get('items'):
                return result['items'][0]['id']

