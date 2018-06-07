import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from ytarchiver.common import ContentItem, StorageManager, Storage


class Sqlite3StorageManager(StorageManager):
    @contextmanager
    def open(self, config) -> 'Sqlite3Storage':
        s = Sqlite3Storage(config.output_dir)
        yield s
        s.close()


class Sqlite3Storage(Storage):
    STORAGE_FILE = 'storage.sqlite'

    def __init__(self, output_directory: str):
        path = os.path.join(output_directory, Sqlite3Storage.STORAGE_FILE)
        storage_exist = os.path.isfile(path)

        self.output_directory = output_directory
        self.connection = sqlite3.connect(path)

        if not storage_exist:
            self._initialise_schema()

    def close(self):
        self.connection.commit()
        self.connection.close()

    def list_videos(self) -> Iterator[ContentItem]:
        cur = self.connection.cursor()
        cur.execute('SELECT video_id, channel_id, timestamp, title, channel_name, filename FROM VIDEOS')
        for columns in cur.fetchall():
            yield ContentItem(*columns)

    def list_livestreams(self) -> Iterator[ContentItem]:
        cur = self.connection.cursor()
        cur.execute('SELECT video_id, channel_id, timestamp, title, channel_name, filename FROM LIVESTREAMS')
        for columns in cur.fetchall():
            yield ContentItem(*columns)

    def video_exist(self, video_id: str):
        cur = self.connection.cursor()
        cur.execute('SELECT 1 FROM VIDEOS WHERE video_id=?', (video_id,))
        return len(list(cur.fetchall())) > 0

    def add_video(self, entry: 'ContentItem'):
        cur = self.connection.cursor()
        cur.execute(
            'INSERT INTO VIDEOS(video_id, channel_id, timestamp, title, channel_name, filename) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (entry.video_id, entry.channel_id, entry.timestamp, entry.title, entry.channel_name, entry.filename)
        )

    def add_livestream(self, entry: 'ContentItem'):
        cur = self.connection.cursor()
        cur.execute(
            'INSERT INTO LIVESTREAMS(video_id, channel_id, timestamp, title, channel_name, filename) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (entry.video_id, entry.channel_id, entry.timestamp, entry.title, entry.channel_name, entry.filename)
        )
        self.commit()

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
        cur.execute(
            'CREATE TABLE LIVESTREAMS('
            'id INTEGER PRIMARY KEY AUTOINCREMENT,'
            'video_id VARCHAR(16), '
            'channel_id VARCHAR(32), '
            'timestamp DATETIME, '
            'title TEXT, '
            'channel_name TEXT, '
            'filename TEXT'
            ')'
        )
        self.connection.commit()
