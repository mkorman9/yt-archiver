import logging
from abc import ABCMeta, abstractmethod
from multiprocessing import Queue, Process
from queue import Empty
from typing import Iterator

from ytarchiver.common import RecordersController, ContentItem, Context, Event
from ytarchiver.download import download_livestream, download_video, DownloadError, LivestreamInterrupted


class RecorderShutdownMessage:
    """
    Message send by recorder after its shutdown
    """

    def __init__(self, recorder_to_shutdown: str):
        self.recorder_to_shutdown = recorder_to_shutdown


class MultiprocessRecordersQueue:
    """
    Queue to communicate recorders running inside different processes
    """

    def __init__(self):
        self._queue = Queue()

    def check_for_messages(self) -> Iterator[RecorderShutdownMessage]:
        try:
            message = RecorderShutdownMessage('')
            while message is not None:
                message = self._queue.get(block=False)
                yield message
        except Empty:
            pass

    def send_message(self, message: RecorderShutdownMessage):
        self._queue.put(message, block=False)


class SynchronousVideoRecordersController(RecordersController):
    """
    Video recorder which runs on thread invoking it. Blocks.
    """

    def __init__(self):
        pass

    def update(self, context: Context):
        pass

    def is_recording_active(self, recording_id: str) -> bool:
        return False

    def start_recording(self, context: Context, item: ContentItem):
        download_video(context, item)
        context.bus.add_event(Event(type=Event.VIDEO_DOWNLOADED, content=item))


class MultiprocessRecordersController(RecordersController, metaclass=ABCMeta):
    """
    Abstract recorder which is able to control multiple processes.
    """

    def __init__(self):
        self.active_recordings = {}
        self.recorders_queue = MultiprocessRecordersQueue()

    def update(self, context: Context):
        for message in self.recorders_queue.check_for_messages():
            self.recording_stopped(context, self.active_recordings[message.recorder_to_shutdown])
            del self.active_recordings[message.recorder_to_shutdown]

    def is_recording_active(self, recording_id: str) -> bool:
        return recording_id in self.active_recordings

    def recording_stopped(self, context: Context, item: ContentItem):
        pass

    @abstractmethod
    def start_recording(self, context: Context, item: ContentItem):
        pass


class MultiprocessLivestreamRecordersController(MultiprocessRecordersController):
    """
    Livestreams recorder which starts new worker process every time it is invoked.
    """

    def __init__(self):
        super(MultiprocessLivestreamRecordersController, self).__init__()

    def recording_stopped(self, context: Context, item: ContentItem):
        context.bus.add_event(Event(type=Event.LIVESTREAM_INTERRUPTED, content=item))

    def start_recording(self, context: Context, item: ContentItem):
        self.active_recordings[item.video_id] = item

        process = Process(
            name='ytarchiver-livestream-recorder',
            target=_livestream_recorder_task,
            args=(item, self.recorders_queue, context.logger)
        )
        process.start()


def _livestream_recorder_task(item: ContentItem, recorders_queue: MultiprocessRecordersQueue, logger: logging.Logger):
    try:
        download_livestream(item, logger)
    except DownloadError:
        logger.exception('error while recording livestream')
    except LivestreamInterrupted as e:
        logger.error('livestream "{}" finished unexpectedly'.format(e.livestream_title))
    finally:
        logger.error('recording of stream "{}" has ended'.format(item.title))
        recorders_queue.send_message(
            RecorderShutdownMessage(recorder_to_shutdown=item.video_id)
        )
