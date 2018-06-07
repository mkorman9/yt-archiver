import logging
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Iterator


class ContentItem:
    """
    Represents either a video or a livestream
    """

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


class RecordersController(metaclass=ABCMeta):
    """
    Abstraction used to schedule and control recordings of various types of content
    """

    @abstractmethod
    def update(self, context):
        pass

    @abstractmethod
    def is_recording_active(self, recording_id: str) -> bool:
        pass

    @abstractmethod
    def start_recording(self, context, item: ContentItem):
        pass


class Storage(metaclass=ABCMeta):
    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def list_videos(self) -> Iterator[ContentItem]:
        pass

    @abstractmethod
    def list_livestreams(self) -> Iterator[ContentItem]:
        pass

    @abstractmethod
    def video_exist(self, video_id: str):
        pass

    @abstractmethod
    def add_video(self, entry: 'ContentItem'):
        pass

    @abstractmethod
    def add_livestream(self, entry: 'ContentItem'):
        pass

    @abstractmethod
    def commit(self):
        pass


class StorageManager(metaclass=ABCMeta):
    @abstractmethod
    def open(self, config) -> Storage:
        pass


class Context:
    def __init__(self,
                 config,
                 logger: logging.Logger,
                 api,
                 video_recorders_controller: RecordersController,
                 livestream_recorders_controller: RecordersController,
                 storage_manager: StorageManager):
        self.config = config
        self.logger = logger
        self.api = api
        self.video_recorders = video_recorders_controller
        self.livestream_recorders = livestream_recorders_controller
        self.storage = storage_manager
