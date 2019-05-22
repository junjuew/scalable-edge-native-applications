from __future__ import absolute_import, division, print_function

import os
import time
import types
import collections

import cv2
import numpy as np
import pandas as pd
from logzero import logger
from rmexp import client, schema, utils
from rmexp.client import dutycycle


class Sensor(object):
    def sample(self):
        pass

    def get(self, idx):
        pass


class VideoSensor(client.RTImageSequenceClient):
    def __init__(self, trace, video_uri=None, *args, **kwargs):
        if video_uri is None:
            video_uri = utils.trace_to_video_uri(trace)
        app = utils.trace_to_app(trace)
        super(VideoSensor, self).__init__(app, video_uri, *args, **kwargs)
        logger.debug('created video sensor to read from: {}'.format(video_uri))

    def sample(self):
        frame = self.get_frame()
        return (self.current_fid, frame)

    def get(self, idx):
        raise NotImplementedError("VideoSensor does not allow ad-hoc query.")


class LegoFSM(object):
    def __init__(self):
        self._state = None
        self._cnt_to_transition = 2
        self._staging_cnt = collections.defaultdict(int)

    def state_change(self, gabriel_msg):
        self._state = gabriel_msg.data
        self._staging_cnt.clear()
        gabriel_msg.data = gabriel_msg.data + '!!State Change!!'

    def process_reply(self, gabriel_msg):
        frame_result = gabriel_msg.data
        if '[[' in frame_result:
            self._staging_cnt[frame_result] += 1
            if self._staging_cnt[frame_result] == self._cnt_to_transition:
                if self._state != frame_result:
                    self.state_change(gabriel_msg)


class VideoAdaptiveSensor(VideoSensor):
    def __init__(self, *args, **kwargs):
        super(VideoAdaptiveSensor, self).__init__(*args, **kwargs)
        # the timestamp of last passive phase trigger condition
        self._last_trigger_time = float("-inf")
        # the timestamp of last sample
        self._last_sample_time = float("-inf")
        app_fsms = {
            'lego': LegoFSM
        }
        assert self._app in app_fsms.keys(), '{} does not have a fsm'.format(self._app)
        self._fsm = app_fsms[self._app]()

    def set_passive_trigger(self):
        self._last_trigger_time = time.time()
        logger.debug('set passive trigger')

    def get_sample_period(self):
        fr = dutycycle.lego_dynamic_sampling_rate(
            time.time() - self._last_trigger_time)
        if abs(fr - self._fps) < 10e-4:
            fr = self._fps
        logger.debug('sample period: {}'.format(fr))
        return 1. / fr

    def sample(self):
        sleep_time = self.get_sample_period() - (time.time() - self._last_sample_time)
        if sleep_time > 1. / self._fps:  # if smaller, get_frame will wait to get next available frame
            logger.debug('passive duty cycle. sleep {}'.format(sleep_time))
            time.sleep(sleep_time)
        frame = self.get_frame()
        self._last_sample_time = time.time()
        return (self.current_fid, frame)

    def process_reply(self, gabriel_msg):
        self._fsm.process_reply(gabriel_msg)
        if '!!State Change!!' in gabriel_msg.data:
            self.set_passive_trigger()


class IMUSensor(Sensor):
    def __init__(self, trace):
        super(IMUSensor, self).__init__()
        self.trace = trace
        df = pd.read_sql('SELECT * FROM IMU WHERE name = %s',
                         schema.engine, params=[self.trace, ])
        df['index'] = df['index'].astype(int)
        self.df = df.sort_values('index')
        df = pd.read_sql('SELECT * FROM IMUSuppression WHERE name = %s',
                         schema.engine, params=[self.trace, ])
        df['index'] = df['index'].astype(int)
        self.df_suppression = df
        self.cur_idx = self.df['index'].iloc[0]
        logger.debug('created IMU sensor {}. Current idx: {}'.format(
            self.trace, self.cur_idx))

    def sample(self):
        self.cur_idx += 1
        return (self.cur_idx, self.get(self.cur_idx))

    def get(self, idx):
        if idx < len(self.df.index):
            return self.df.iloc[idx][['rot_x',
                                      'rot_y',
                                      'rot_z',
                                      'acc_x',
                                      'acc_y',
                                      'acc_z']].values
        else:
            logger.warning(
                """imu look up idx ({}) invalid. 
                A single of this warning might due to h264 encoding requires even number of frames""".format(idx))
            return np.array([0.]*6)

    def is_passive(self, idx):
        if idx < len(self.df_suppression.index):
            return self.df_suppression.iloc[idx][['suppression']].values == '1'
        else:
            logger.warning(
                """imu is_passive look up idx ({}) invalid. 
                A single of this warning might due to h264 encoding requires even number of frames""".format(idx))
            return False


class MobileDevice(object):
    def __init__(self, sensors):
        super(MobileDevice, self).__init__()
        self.sensors = sensors

    def sample(self):
        return map(lambda x: x.sample(), self.sensors)


class CameraTimedMobileDevice(MobileDevice):
    """For each sample it get fid from Video sensor and return
    corresponding other sensor data.
    """

    def __init__(self, sensors):
        super(CameraTimedMobileDevice, self).__init__(sensors)
        assert (isinstance(self.sensors[0], VideoSensor))
        self.primary_sensor = self.sensors[0]
        self.secondary_sensors = self.sensors[1:]

    def sample(self):
        (idx, pdata) = self.primary_sensor.sample()
        data = map(lambda x: x.get(idx), self.secondary_sensors)
        data = zip([idx]*len(data), data)
        data.insert(0, (idx, pdata))
        return data


class IMUSuppresedCameraTimedMobileDevice(CameraTimedMobileDevice):
    """For each sample, it gets fid from Video sensor and 
    checks if such sample should be suppressed from IMU suppression.
    """

    def __init__(self, sensors):
        super(IMUSuppresedCameraTimedMobileDevice, self).__init__(sensors)
        self.imu = self.sensors[1]

    def sample(self):
        (idx, pdata) = self.primary_sensor.sample()
        suppression = self.imu.is_passive(idx)
        while suppression:
            logger.debug('suppress sample: {}'.format(idx))
            (idx, pdata) = self.primary_sensor.sample()
            suppression = self.imu.is_passive(idx)

        data = map(lambda x: x.get(idx), self.secondary_sensors)
        data = zip([idx]*len(data), data)
        data.insert(0, (idx, pdata))
        return data


class DeviceToClientAdapter(object):
    """An adapter that make devices work with previous Client apis in video.py 
    """

    def __init__(self, device):
        super(DeviceToClientAdapter, self).__init__()
        self.device = device

    def get_and_send_frame(self, **kwargs):
        data = self.device.sample()
        fid, frame = data[0]
        frame_bytes = None
        if isinstance(self.device.primary_sensor, client.RTImageSequenceClient):
            frame_bytes = frame
        elif isinstance(self.device.primary_sensor, client.RTVideoClient):
            frame_bytes = cv2.imencode('.jpg', frame)[1].tostring()
        else:
            raise TypeError('{} is not supported by the DeviceToClientAdapter'.format(
                type(self.device.primary_sensor)))
        ts = time.time()
        self.device.primary_sensor.send_frame(
            frame_bytes, fid, time=ts, **kwargs)

    def process_reply(self, msg):
        # let the primary sensor to determine how to adjust to reply
        self.device.primary_sensor.process_reply(msg)


def test_device():
    trace = 'lego-tr6'
    cam = VideoAdaptiveSensor(trace)
    imu = IMUSensor(trace)
    d = IMUSuppresedCameraTimedMobileDevice(
        sensors=[cam, imu]
    )
    idx = 0
    while True:
        time.sleep(0.100)
        # logger.info(d.sample())
        d.sample()
        logger.info('sampled at {}.'.format(time.time()))
        idx += 1
        if idx == 20:
            logger.info('set passive trigger {}.'.format(time.time()))
            cam.set_passive_trigger()


if __name__ == "__main__":
    test_device()
