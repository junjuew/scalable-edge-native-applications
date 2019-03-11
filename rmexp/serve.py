#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import ast
import collections
import multiprocessing
import os
import time

import cv2
import fire
import numpy as np
from logzero import logger

import redis
from rmexp import config, worker


class RedisConnector(object):
    def __init__(self, host, port, db=0):
        super(RedisConnector, self).__init__()
        self.client = redis.Redis(host=host, port=port, db=db)

    def get(self):
        # blocking
        item = self.client.brpop([config.REDIS_STREAM_CHAN])
        return item


class JobQueue(object):
    def __init__(self, connector):
        super(JobQueue, self).__init__()
        self.connector = connector

    def get(self):
        return self.connector.get()


def start_process_loop(host, port):
    jq = JobQueue(RedisConnector(host, port))
    loop = worker.lego_loop
    loop(jq)


def start(num, host, port):
    procs = [multiprocessing.Process(target=start_process_loop, args=(
        host, port, )) for i in range(num)]
    map(lambda proc: proc.start(), procs)
    map(lambda proc: proc.join(), procs)


if __name__ == "__main__":
    fire.Fire()