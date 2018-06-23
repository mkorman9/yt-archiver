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

    def __eq__(self, other):
        return self.video_id == other.video_id


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
    """
    Storage for metadata of videos and livestreams
    """

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
    """
    Abstraction to open Storage based on given configuration
    """

    @abstractmethod
    def open(self, config) -> Storage:
        pass


class Event:
    """
    Represents system event
    """

    NEW_VIDEO = 0
    VIDEO_DOWNLOADED = 1
    LIVESTREAM_STARTED = 2
    LIVESTREAM_INTERRUPTED = 3

    def __init__(self, type: int, content: ContentItem):
        self.type = type
        self.content = content

    def __eq__(self, other):
        return self.type == other.type and self.content == other.content


class EventBus:
    """
    EventBus collects and stores events from entire system
    """

    def __init__(self):
        self._queue = []

    def retrieve_events(self) -> Iterator[Event]:
        while len(self._queue) > 0:
            yield self._queue.pop()

    def add_event(self, event: Event):
        self._queue.append(event)


class Plugin(metaclass=ABCMeta):
    """
    Plugable component able to react to system events
    """

    @abstractmethod
    def on_event(self, event: Event, is_first_run: bool):
        pass


class PluginsManager:
    """
    Manager for all registered plugins
    """

    def __init__(self):
        self._plugins = []

    def register_plugin(self, plugin: Plugin):
        self._plugins.append(plugin)

    def on_event(self, event: Event, is_first_run: bool):
        for plugin in self._plugins:
            plugin.on_event(event, is_first_run)


class Context:
    """
    Execution context of application
    """

    def __init__(self,
                 config,
                 logger: logging.Logger,
                 api,
                 video_recorders_controller: RecordersController,
                 livestream_recorders_controller: RecordersController,
                 storage_manager: StorageManager,
                 bus: EventBus,
                 plugins: PluginsManager):
        self.config = config
        self.logger = logger
        self.api = api
        self.video_recorders = video_recorders_controller
        self.livestream_recorders = livestream_recorders_controller
        self.storage = storage_manager
        self.bus = bus
        self.plugins = plugins
