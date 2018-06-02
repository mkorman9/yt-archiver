import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator, List

from ytarchiver.common import Video, Context

STORAGE_FILE = 'storage.sqlite'


class Storage:
    def __init__(self, output_directory: str, initialise: bool=True):
        path = os.path.join(output_directory, STORAGE_FILE)
        storage_exist = os.path.isfile(path)

        self.output_directory = output_directory
        self.connection = sqlite3.connect(path)

        if initialise and not storage_exist:
            self._initialise_schema()

    def close(self):
        self.connection.commit()
        self.connection.close()

    def list_videos(self) -> Iterator[Video]:
        cur = self.connection.cursor()
        cur.execute('SELECT video_id, channel_id, timestamp, title, channel_name, filename FROM VIDEOS')
        for columns in cur.fetchall():
            yield Video(*columns)

    def video_exist(self, video_id: str):
        cur = self.connection.cursor()
        cur.execute('SELECT 1 FROM VIDEOS WHERE video_id=?', (video_id,))
        return len(list(cur.fetchall())) > 0

    def add_video(self, entry: 'Video'):
        cur = self.connection.cursor()
        cur.execute(
            'INSERT INTO VIDEOS(video_id, channel_id, timestamp, title, channel_name, filename) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (entry.video_id, entry.channel_id, entry.timestamp, entry.title, entry.channel_name, entry.filename)
        )

    def commit(self):
        self.connection.commit()

    def _initialise_schema(self):
        cur = self.connection.cursor()
        cur.execute(
            'CREATE TABLE VIDEOS('
            'video_id VARCHAR(16) PRIMARY KEY, '
            'channel_id VARCHAR(32), '
            'timestamp DATETIME, '
            'title TEXT, '
            'channel_name TEXT, '
            'filename TEXT'
            ')'
        )
        self.connection.commit()


@contextmanager
def open_storage(directory: str, initialise: bool=True) -> Storage:
    s = Storage(directory, initialise=initialise)
    yield s
    s.close()


def get_saved_videos(context: Context) -> List[Video]:
    storage_path = os.path.join(context.config.output_dir, STORAGE_FILE)
    if not os.path.isfile(storage_path):
        context.logger.warning('storage file does not exist: ' + storage_path)
        return []

    with open_storage(context.config.output_dir, initialise=False) as s:
        return list(s.list_videos())
