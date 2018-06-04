import logging
from abc import ABCMeta, abstractmethod
from multiprocessing import Queue, Process
from queue import Empty
from typing import Iterator

from ytarchiver.common import RecordersController, ContentItem, Context
from ytarchiver.download import record_livestream, download_video


class RecorderShutdownMessage:
    def __init__(self, recorder_to_shutdown: str):
        self.recorder_to_shutdown = recorder_to_shutdown


class MultiprocessRecordersQueue:
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
    def __init__(self):
        pass

    def update(self, context: Context):
        pass

    def is_recording_active(self, recording_id: str) -> bool:
        return False

    def start_recording(self, context: Context, item: ContentItem):
        download_video(context, item)


class MultiprocessRecordersController(RecordersController, metaclass=ABCMeta):
    def __init__(self):
        self.active_recordings = {}
        self.recorders_queue = MultiprocessRecordersQueue()

    def update(self, context: Context):
        for message in self.recorders_queue.check_for_messages():
            del self.active_recordings[message.recorder_to_shutdown]

    def is_recording_active(self, recording_id: str) -> bool:
        return recording_id in self.active_recordings

    @abstractmethod
    def start_recording(self, context: Context, item: ContentItem):
        pass


class MultiprocessLivestreamRecordersController(MultiprocessRecordersController):
    def __init__(self):
        super(MultiprocessLivestreamRecordersController, self).__init__()

    def start_recording(self, context: Context, item: ContentItem):
        self.active_recordings[item.video_id] = True  # replace boolean with any other information about recording

        process = Process(
            name='ytarchiver-livestream-recorder',
            target=_livestream_recorder_task,
            args=(item, self.recorders_queue, context.logger)
        )
        process.start()


def _livestream_recorder_task(item: ContentItem, recorders_queue: MultiprocessRecordersQueue, logger: logging.Logger):
    try:
        record_livestream(item, logger)
    except (IOError, EOFError):
        logger.error('stream "{}" finished unexpectedly'.format(item.title))
    except Exception as e:
        logger.error('error while recording stream "{}"'.format(item.title))
        logger.error(e)
    finally:
        logger.error('recording of stream "{}" has ended'.format(item.title))
        recorders_queue.send_message(
            RecorderShutdownMessage(recorder_to_shutdown=item.video_id)
        )
