import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

STORAGE_FILE = 'storage.sqlite'


class Entry:
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

    def list(self) -> Iterator[Entry]:
        cur = self.connection.cursor()
        cur.execute('SELECT video_id, channel_id, timestamp, title, channel_name, filename FROM VIDEOS')
        for columns in cur.fetchall():
            yield Entry(*columns)

    def exist(self, video_id):
        cur = self.connection.cursor()
        cur.execute('SELECT 1 FROM VIDEOS WHERE video_id=?', (video_id,))
        return len(list(cur.fetchall())) > 0

    def add(self, entry: 'Entry'):
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
def open_storage(directory: str, initialise: bool=True):
    s = Storage(directory, initialise=initialise)
    yield s
    s.close()


def get_saved_entries(config, logger):
    storage_path = os.path.join(config.output_dir, STORAGE_FILE)
    if not os.path.isfile(storage_path):
        logger.warning('storage file does not exist: ' + storage_path)
        return []

    with open_storage(config.output_dir, initialise=False) as s:
        return list(s.list())
