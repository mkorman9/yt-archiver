import logging
from typing import Any

from googleapiclient.errors import HttpError

from ytarchiver.api import find_channel_uploaded_videos, fetch_channel_livestream, find_channels_list
from ytarchiver.common import Context
from ytarchiver.download import generate_livestream_filename, generate_video_filename
from ytarchiver.storage import open_storage, Storage


def lookup(context: Context, is_first_run: bool):
    statistics = _Statistics(
        is_first_run=is_first_run,
        monitor_livestreams=context.config.monitor_livestreams
    )

    context.livestream_recorders.update(context)
    context.video_recorders.update(context)

    with open_storage(context.config.output_dir) as storage:
        channels = find_channels_list(context)
        for channel_id, channel_content in channels:
            _fetch_channel_content(context, channel_id, channel_content, storage, statistics, is_first_run)
            storage.commit()

    statistics.announce(context.logger)


def _fetch_channel_content(
        context: Context,
        channel_id: str,
        channel_content: Any,
        storage: Storage, statistics,
        is_first_run: bool=False):
    try:
        _check_for_livestreams(context, channel_id, statistics, storage)
        _check_for_videos(context, channel_content, is_first_run, statistics, storage)
    except ConnectionError as e:
        context.logger.error('connection to API has failed, skipping lookup')
        context.logger.error(e)
    except HttpError as e:
        context.logger.error('API call has failed, skipping lookup')
        context.logger.error(e)
    except Exception as e:
        context.logger.error('unknown error')
        context.logger.error(e)


def _check_for_livestreams(context: Context, channel_id: str, statistics: '_Statistics', storage: Storage):
    if not context.config.monitor_livestreams:
        return

    livestream = fetch_channel_livestream(context, channel_id)
    if livestream is not None:
        if not context.livestream_recorders.is_recording_active(livestream.video_id):
            livestream.filename = generate_livestream_filename(context.config.output_dir, livestream)
            context.logger.info('new livestream "{}"'.format(livestream.title))
            context.livestream_recorders.start_recording(context, livestream)
            storage.add_livestream(livestream)
        statistics.notify_active_livestream()


def _check_for_videos(context: Context,
                      channel_content: Any,
                      is_first_run: bool,
                      statistics: '_Statistics',
                      storage: Storage):
    for video in find_channel_uploaded_videos(context, channel_content, is_first_run):
        video_not_registered = not storage.video_exist(video.video_id) and \
                               not context.video_recorders.is_recording_active(video.video_id)
        if video_not_registered:
            video.filename = generate_video_filename(context.config.output_dir, video)
            context.logger.info('new video "{}"'.format(video.title))
            if not is_first_run or context.config.archive_all:
                context.video_recorders.start_recording(context, video)
            storage.add_video(video)
        statistics.notify_video(new=video_not_registered)


class _Statistics:
    def __init__(self, is_first_run: bool, monitor_livestreams: bool):
        self.is_first_run = is_first_run
        self.monitor_livestreams = monitor_livestreams
        self.total_videos = 0
        self.new_videos = 0
        self.active_livestreams = 0

    def notify_video(self, new: bool=False):
        self.total_videos += 1
        if new:
            self.new_videos += 1

    def notify_active_livestream(self):
        self.active_livestreams += 1

    def announce(self, logger: logging.Logger):
        logger.info(
            '{} videos: {}, new: {}, active livestreams: {}'.format(
                'total' if self.is_first_run else 'fetched',
                self.total_videos,
                self.new_videos,
                self.active_livestreams if self.monitor_livestreams else 'N/A'
            )
        )
