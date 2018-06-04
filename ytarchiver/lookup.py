import logging

from googleapiclient.errors import HttpError

from ytarchiver.api import find_channel_uploaded_videos, fetch_channel_livestream
from ytarchiver.common import Context
from ytarchiver.download import generate_livestream_filename, generate_video_filename
from ytarchiver.storage import open_storage, Storage


class Statistics:
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


def lookup(context: Context, is_first_run: bool):
    statistics = Statistics(
        is_first_run=is_first_run,
        monitor_livestreams=context.config.monitor_livestreams
    )

    context.livestream_recorders.update(context)
    context.video_recorders.update(context)

    with open_storage(context.config.output_dir) as storage:
        for channel_id in context.config.channels_list:
            _fetch_channel_content(context, channel_id, storage, statistics, is_first_run)

    statistics.announce(context.logger)


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
        if not context.livestream_recorders.is_recording_active(livestream.video_id):
            livestream.filename = generate_livestream_filename(context.config.output_dir, livestream)
            context.logger.info('new livestream "{}"'.format(livestream.title))
            context.livestream_recorders.start_recording(context, livestream)
            storage.add_livestream(livestream)
        statistics.notify_active_livestream()


def _check_for_videos(context: Context, channel_id: str, is_first_run: bool, statistics: Statistics, storage: Storage):
    for video in find_channel_uploaded_videos(context, channel_id, is_first_run):
        video_not_registered = not storage.video_exist(video.video_id) and \
                               not context.video_recorders.is_recording_active(video.video_id)
        if video_not_registered:
            video.filename = generate_video_filename(context.config.output_dir, video)
            context.logger.info('new video "{}"'.format(video.title))
            if not is_first_run or context.config.archive_all:
                context.video_recorders.start_recording(context, video)
            storage.add_video(video)
        statistics.notify_video(new=video_not_registered)
