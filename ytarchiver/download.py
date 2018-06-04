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
LIVESTREAM_CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB


def sanitize_filename(filename):
    filename = safe_filename(filename)
    filename = filename.replace(' ', '_')
    return filename.encode('ascii', 'ignore').decode('ascii')


def generate_livestream_filename(output_path: str, livestream: ContentItem):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    filename = '{}_{}.{}'.format(now, sanitize_filename(livestream.title), 'ts')
    return os.path.join(output_path, filename)


def generate_video_filename(output_path: str, video: ContentItem):
    filename = '{}_{}.{}'.format(video.timestamp, sanitize_filename(video.title), 'mp4')
    return os.path.join(output_path, filename)


def record_livestream(livestream: ContentItem, logger: logging.Logger):
    url = YOUTUBE_URL_PREFIX + livestream.video_id
    available_streams = streamlink.api.streams(url)

    best_resolution = ''
    for resolution in SUPPORTED_LIVESTREAM_RESOLUTIONS:
        if resolution in available_streams:
            best_resolution = resolution
            break
    if best_resolution == '':
        logger.error('no supported resolution found for "{}"'.format(livestream.title))
        return

    stream = available_streams[best_resolution]

    logging.error('recording {}:{} stream of "{}"'.format(stream.shortname(), best_resolution, livestream.title))
    with open(livestream.filename, 'wb') as out:
        try:
            with stream.open() as handle:
                while True:
                    buffer = handle.read(LIVESTREAM_CHUNK_SIZE)
                    out.write(buffer)
                    out.flush()
                    time.sleep(0)
        except Exception:
            out.flush()
            raise


def download_video(context: Context, video: ContentItem):
    download_link = YOUTUBE_URL_PREFIX + video.video_id
    total_size = 0

    def on_progress(stream, chunk, handle, bytes_remaining):
        context.logger.debug('progress... {}/{}'.format(total_size - bytes_remaining, total_size))

    def on_complete(stream, handle):
        context.logger.debug('download of "{}" complete'.format(video.title))

    yt = YouTube(download_link)
    yt.register_on_complete_callback(on_complete)
    yt.register_on_progress_callback(on_progress)
    streams = yt.streams.all()
    stream = _choose_best_video_stream(streams)
    total_size = stream.filesize

    context.logger.info('started downloading "{}"'.format(video.title))
    stream.download(
        output_path=os.path.dirname(video.filename),
        filename=os.path.splitext(os.path.basename(video.filename))[0]
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
