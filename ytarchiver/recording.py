import logging
from multiprocessing import Queue, Process
from queue import Empty
from typing import Iterator

from ytarchiver.common import Recordings, RecorderMessage, Video
from ytarchiver.download import record_livestream


class MultiprocessRecordingsController(Recordings):
    def __init__(self):
        self.active_recordings = {}
        self.recorders_queue = MultiprocessRecordersQueue()

    def update(self, logger: logging.Logger):
        for message in self.recorders_queue.check_for_messages():
            del self.active_recordings[message.recorder_to_shutdown]

    def is_recording_active(self, recording_id: str) -> bool:
        return recording_id in self.active_recordings

    def create_recording(self, stream: Video, logger: logging.Logger):
        self.active_recordings[stream.video_id] = True  # replace boolean with any other information about recording

        process = Process(target=_recorder_task, args=(stream, self.recorders_queue, logger))
        process.start()


class MultiprocessRecordersQueue:
    def __init__(self):
        self._queue = Queue()

    def check_for_messages(self) -> Iterator[RecorderMessage]:
        try:
            message = RecorderMessage('')
            while message is not None:
                message = self._queue.get(block=False)
                yield message
        except Empty:
            pass

    def send_message(self, message: RecorderMessage):
        self._queue.put(message, block=False)


def _recorder_task(stream: Video, recorders_queue: MultiprocessRecordersQueue, logger: logging.Logger):
    try:
        record_livestream(stream, logger)
    except (IOError, EOFError):
        logger.error('stream "{}" finished unexpectedly'.format(stream.title))
    except Exception as e:
        logger.error('error while recording stream "{}"'.format(stream.title))
        logger.error(e)
    finally:
        logger.error('recording of stream "{}" has ended'.format(stream.title))
        recorders_queue.send_message(
            RecorderMessage(recorder_to_shutdown=stream.video_id)
        )
