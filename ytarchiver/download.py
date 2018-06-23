import logging
import os
import time

import streamlink
from datetime import datetime
from pytube import YouTube
from pytube.helpers import safe_filename

from ytarchiver.common import ContentItem, Context

YOUTUBE_URL_PREFIX = 'https://www.youtube.com/watch?v='
SUPPORTED_LIVESTREAM_RESOLUTIONS = ['720p', '480p', '360p', '240p', '144p']
MEGABYTE = 1024 * 1024
LIVESTREAM_CHUNK_SIZE = 4 * MEGABYTE


class DownloadError(Exception):
    """
    Error caused by stream download
    """

    def __init__(self, title, cause):
        super(DownloadError, self).__init__(title, cause)


class LivestreamInterruptedError(Exception):
    """
    Error caused when livestream is interrupted unexpectedly
    """

    def __init__(self, title, cause):
        super(LivestreamInterruptedError, self).__init__(title, cause)


def download_video(context: Context, video: ContentItem):
    """
    Starts downloading specified video to disk. Blocks.

    :param context: execution context
    :param video: video to download
    :exception DownloadError
    """
    try:
        download_callback = _VideoDownloadCallback(
            context=context,
            video=video
        )
        yt = YouTube(
            YOUTUBE_URL_PREFIX + video.video_id,
            on_complete_callback=download_callback.on_complete,
            on_progress_callback=download_callback.on_progress
        )

        streams = yt.streams.all()
        stream = _choose_best_video_stream(streams)
        download_callback.total_video_size = stream.filesize

        context.logger.info('started downloading video "{}"'.format(video.title))
        stream.download(
            output_path=os.path.dirname(video.filename),
            filename=os.path.splitext(os.path.basename(video.filename))[0]
        )
    except Exception as e:
        raise DownloadError(video.title, e)


def download_livestream(livestream: ContentItem, logger: logging.Logger):
    """
    Starts recording given livestream. Blocks until the stream is finished or error occurs.

    :param livestream: livestream to record
    :param logger: logger to write error messages to
    :exception DownloadError
    :exception LivestreamInterruptedError
    """
    try:
        url = YOUTUBE_URL_PREFIX + livestream.video_id
        available_streams = streamlink.api.streams(url)
        best_resolution = _choose_best_livestream_resolution(available_streams)
        if best_resolution is None:
            logger.error('no supported resolution found for "{}"'.format(livestream.title))
            return

        stream = available_streams[best_resolution]

        logging.error('recording {}:{} stream of "{}"'.format(stream.shortname(), best_resolution, livestream.title))
        with open(livestream.filename, 'wb') as out:
            with stream.open() as handle:
                while True:
                    buffer = handle.read(LIVESTREAM_CHUNK_SIZE)
                    out.write(buffer)
                    out.flush()
                    time.sleep(0)
    except (IOError, EOFError) as e:
        raise LivestreamInterruptedError(livestream.title, e)
    except Exception as e:
        raise DownloadError(livestream.title, e)


def sanitize_filename(s: str) -> str:
    """
    Processes given string, making it safe to be a correct filename.

    :param s: input string
    :return: string safe for filesystem
    """
    s = safe_filename(s)
    s = s.replace(' ', '_')
    return s.encode('ascii', 'ignore').decode('ascii')


def generate_livestream_filename(output_path: str, livestream: ContentItem):
    """
    Generates path to save given livestream. Sanitizes title.

    :param output_path: output directory
    :param livestream: livestream to generate filename from
    :return: path containing current timestamp and sanitized livestream title
    """
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    filename = '{}_{}.{}'.format(now, sanitize_filename(livestream.title), 'ts')
    return os.path.join(output_path, filename)


def generate_video_filename(output_path: str, video: ContentItem):
    """
    Generates path to save given video. Sanitizes title.

    :param output_path: output directory
    :param video: video to generate filename from
    :return: path containing sanitized video title
    """
    filename = '{}_{}.{}'.format(video.timestamp, sanitize_filename(video.title), 'mp4')
    return os.path.join(output_path, filename)


class _VideoDownloadCallback:
    PROGRESS_MESSAGES_LIMIT = 5

    def __init__(self, context: Context, video: ContentItem, total_video_size: int=0):
        self._context = context
        self._video = video
        self.total_video_size = total_video_size
        self.__progress_callback_counter = 0

    def on_progress(self, stream, chunk, handle, bytes_remaining):
        self.__progress_callback_counter += 1
        if self.__progress_callback_counter != _VideoDownloadCallback.PROGRESS_MESSAGES_LIMIT:
            return
        self.__progress_callback_counter = 0

        self._context.logger.debug(
            'downloading video "{}"... {:.2f}/{:.2f} MB'.format(
                self._video.title,
                (self.total_video_size - bytes_remaining) / MEGABYTE,
                self.total_video_size / MEGABYTE
            )
        )

    def on_complete(self, stream, handle):
        self._context.logger.debug(
            'download of video "{}" is complete'.format(
                self._video.title
            )
        )


def _choose_best_video_stream(streams):
    best_stream = None
    for stream in streams:
        if stream.includes_audio_track and stream.includes_video_track:
            if best_stream is None:
                best_stream = stream

            higher_resolution = stream.resolution > best_stream.resolution
            equal_resolution = stream.resolution == best_stream.resolution
            better_format = 'mp4' in stream.mime_type and 'mp4' not in best_stream.mime_type
            if better_format and (equal_resolution or higher_resolution):
                best_stream = stream
            if higher_resolution:
                best_stream = stream

    return best_stream


def _choose_best_livestream_resolution(streams):
    best_resolution = None
    for resolution in SUPPORTED_LIVESTREAM_RESOLUTIONS:
        if resolution in streams:
            best_resolution = resolution
            break

    return best_resolution
