import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime


class Video:
    def __init__(self,
                 video_id: str,
                 channel_id: str,
                 timestamp: datetime,
                 title: str,
                 channel_name: str,
                 filename: str=None):
        self.video_id = video_id
        self.channel_id = channel_id
        self.timestamp = timestamp
        self.title = title
        self.channel_name = channel_name
        self.filename = filename

    def __str__(self):
        return '{}\t{}\t{}\t{}\t{}\t{}'.format(
            self.video_id,
            self.channel_id,
            self.timestamp,
            self.title,
            self.channel_name,
            self.filename
        )

    def __repr__(self):
        return self.__str__()


class Recordings(metaclass=ABCMeta):
    @abstractmethod
    def update(self, logger: logging.Logger):
        pass

    @abstractmethod
    def is_recording_active(self, recording_id: str) -> bool:
        pass

    @abstractmethod
    def create_recording(self, stream: Video, logger: logging.Logger):
        pass


class RecorderMessage:
    def __init__(self, recorder_to_shutdown: str):
        self.recorder_to_shutdown = recorder_to_shutdown


class Context:
    def __init__(self, config, logger: logging.Logger, recordings_controller: Recordings):
        self.config = config
        self.logger = logger
        self.service = None
        self.recordings = recordings_controller
