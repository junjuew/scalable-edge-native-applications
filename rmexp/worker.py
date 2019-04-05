from __future__ import absolute_import, division, print_function

import ast
import logging
import os
import time

import cv2
import fire
import lego
import logzero
import numpy as np
from logzero import logger
from rmexp import config, dbutils, gabriel_pb2
from rmexp.schema import models

logzero.loglevel(logging.DEBUG)


def lego_loop(job_queue):
    lego_app = lego.LegoHandler()
    sess = dbutils.get_session()
    while True:
        (tag, msg) = job_queue.get()
        gabriel_msg = gabriel_pb2.Message()
        gabriel_msg.ParseFromString(msg)
        encoded_im, ts = gabriel_msg.data, gabriel_msg.timestamp
        encoded_im_np = np.asarray(bytearray(encoded_im), dtype=np.uint8)
        img = cv2.imdecode(encoded_im_np, cv2.CV_LOAD_IMAGE_UNCHANGED)
        result = lego_app.process(img)
        finished_t = time.time()
        time_lapse = (finished_t - ts) * 1000
        logger.debug(result)
        logger.debug('[proc {}] takes {} ms for an item'.format(
            os.getpid(), (time.time() - ts) * 1000))
        record, _ = dbutils.get_or_create(sess, models.LegoLatency,
                                          name=config.EXP, index=gabriel_msg.index)
        record.finished = finished_t
        record.val = time_lapse
        sess.commit()


def batch_process(video_uri, store_result=False, store_latency=False):
    lego_app = lego.LegoHandler()
    cam = cv2.VideoCapture(video_uri)
    has_frame = True
    sess = dbutils.get_session()
    while has_frame:
        ts = time.time()
        has_frame, img = cam.read()
        if img is not None:
            result = lego_app.process(img)
            time_lapse = (time.time() - ts) * 1000
            if store_result:
                sess.add(models.SS(
                    name=config.EXP,
                    val=str(result),
                    trace=os.path.basename(os.path.dirname(video_uri))))
            if store_latency:
                sess.add(models.LegoLatency(
                    name=config.EXP, val=int(time_lapse)))
            sess.commit()
            logger.debug(result)


if __name__ == "__main__":
    fire.Fire()
