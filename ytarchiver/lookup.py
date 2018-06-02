from datetime import datetime

import os
from googleapiclient.errors import HttpError
from pytube.helpers import safe_filename

from ytarchiver.api import find_channel_uploaded_videos, fetch_channel_livestream
from ytarchiver.common import Context, Video
from ytarchiver.download import download_video
from ytarchiver.storage import open_storage, Storage


class Statistics:
    def __init__(self):
        self.total_videos = 0
        self.new_videos = 0
        self.active_livestreams = 0

    def notify_video(self, new: bool=False):
        self.total_videos += 1
        if new:
            self.new_videos += 1

    def notify_active_livestream(self):
        self.active_livestreams += 1


def lookup(context: Context, is_first_run: bool):
    statistics = Statistics()

    context.recordings.update(context.logger)

    with open_storage(context.config.output_dir) as storage:
        for channel_id in context.config.channels_list:
            _fetch_channel_content(context, channel_id, storage, statistics, is_first_run)

    context.logger.info(
        'total videos: {}, new: {}, active livestreams {}'.format(
            statistics.total_videos,
            statistics.new_videos,
            statistics.active_livestreams if context.config.monitor_livestreams else 'N/A'
        )
    )


def _fetch_channel_content(context: Context, channel_id: str, storage: Storage, statistics, is_first_run: bool=False):
    try:
        _check_for_livestreams(context, channel_id, statistics, storage)
        _check_for_videos(context, channel_id, is_first_run, statistics, storage)
    except ConnectionError as e:
        context.logger.error('connection to API has failed, skipping lookup')
        context.logger.error(e)
        return
    except HttpError as e:
        context.logger.error('API call has failed, skipping lookup')
        context.logger.error(e)
        return
    finally:
        storage.commit()


def _check_for_livestreams(context: Context, channel_id: str, statistics: Statistics, storage: Storage):
    if not context.config.monitor_livestreams:
        return

    livestream = fetch_channel_livestream(context, channel_id)
    if livestream is not None:
        if not context.recordings.is_recording_active(livestream.video_id):
            livestream.filename = _generate_livestream_filename(context, livestream)
            context.logger.info('new livestream "{}"'.format(livestream.title))
            context.recordings.create_recording(livestream, context.logger)
            storage.add_livestream(livestream)
        statistics.notify_active_livestream()


def _check_for_videos(context: Context, channel_id: str, is_first_run: bool, statistics: Statistics, storage: Storage):
    for video in find_channel_uploaded_videos(context, channel_id):
        video_not_registered = not storage.video_exist(video.video_id)
        if video_not_registered:
            _register_video(context, storage, video, is_first_run)
        statistics.notify_video(new=video_not_registered)


def _register_video(context: Context, storage: Storage, video: Video, is_first_run: bool=False):
    should_be_downloaded = not is_first_run or context.config.archive_all

    context.logger.info('new video "{}"'.format(video.title))

    if should_be_downloaded:
        file_path = download_video(context, video)
        video.filename = file_path

    storage.add_video(video)

    if should_be_downloaded:
        storage.commit()


def _generate_livestream_filename(context: Context, livestream: Video):
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    filename = '{} {}.{}'.format(now, safe_filename(livestream.title), 'ts')
    return os.path.join(context.config.output_dir, filename)
