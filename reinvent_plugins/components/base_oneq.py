from __future__ import annotations

import tempfile
import os
from time import sleep
from typing import List, Optional, Union

import numpy as np
from loguru import logger
from requests import get, post

from .component_results import ComponentResults


class BaseOneq:

    def __init__(self, bearer: Optional[str] = None):
        if bearer:
            self.bearer = bearer
        elif bearer := os.getenv("BEARER"):
            self.bearer = bearer
        else:
            raise ValueError("Bearer value should be provided")
        self.headers = {"Authorization": self.bearer}

    def __call__(self, smilies: List[str]) -> np.array:
        logger.info(f"module {self.pipeline} working")
        scores = []
        tasks = []
        for smi in smilies:
            logger.info(f"smi{smi}")
            task_id = self.set_task(smi)
            logger.info(f"smi{smi}, taskid {task_id}")
            tasks.append(task_id)
        scores.append(np.array([self.get_task(task_id=task) for task in tasks]))

        return ComponentResults(scores)

    def set_task(self, smi):
        # set task
        with tempfile.NamedTemporaryFile(delete=False, suffix=".smi") as tmp:
            content = f"{smi} reinvent\n".encode("utf-8")
            tmp.write(content)
        for _ in range(5):
            with open(tmp.name) as file:
                response = post(f"https://chemlab-back.dev.net.biocad.ru/v1/molprop/run-pipeline/{self.pipeline}/",
                                headers=self.headers, files={"file": file})
            logger.info(response)
            if response.status_code == 200:
                break
            sleep(10)
        task_id = response.json()["task_id"]
        return task_id

    def status_ok(self, task_id):
        return get(f"https://chemlab-back.dev.net.biocad.ru/v1/molprop/task/{task_id}/status/",
                   headers=self.headers).status_code == 200

    def get_task(self, task_id, sleep_time=10, give_up_time=3600) -> Union[np.float, np.nan, np.int]:
        # get results
        for _ in range(give_up_time // sleep_time):
            if self.status_ok(task_id=task_id):
                result = get(f"https://chemlab-back.dev.net.biocad.ru/v1/molprop/task/{task_id}/result/",
                             headers=self.headers)
                logger.info(f"{task_id} not ready, sleep for 10 sec")
                if bool(result.json()):
                    logger.info(result.json())
                    if self.classification:
                        return np.int(result.json()[0][self.field])
                    else:
                        return np.float(result.json()[0][self.field])
            sleep(sleep_time)
        return np.nan
