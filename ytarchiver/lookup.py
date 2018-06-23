import logging

from ytarchiver.api import YoutubeChannel, APIError
from ytarchiver.common import Context, Event
from ytarchiver.download import generate_livestream_filename, generate_video_filename, DownloadError, \
    LivestreamInterrupted
from ytarchiver.sqlite import Sqlite3Storage


def lookup(context: Context, is_first_run: bool):
    statistics = _Statistics(
        is_first_run=is_first_run,
        monitor_livestreams=context.config.monitor_livestreams
    )

    context.livestream_recorders.update(context)
    context.video_recorders.update(context)

    with context.storage.open(context.config) as storage:
        try:
            channels = context.api.find_channels(context.config.channels_list)
            for channel in channels:
                _fetch_channel_content(context, channel, storage, statistics, is_first_run)
                storage.commit()
        except APIError:
            context.logger.exception('error while making API call')
        except DownloadError:
            context.logger.exception('error while downloading')
        except LivestreamInterrupted as e:
            context.logger.error('livestream "{}" finished unexpectedly'.format(e.livestream_title))
        except Exception:
            context.logger.exception('unknown error')

    statistics.announce(context.logger)
    _process_events(context, is_first_run)


def _fetch_channel_content(
        context: Context,
        channel: YoutubeChannel,
        storage: Sqlite3Storage, statistics,
        is_first_run: bool=False):
    _check_for_livestreams(context, channel, statistics, storage)
    _check_for_videos(context, channel, is_first_run, statistics, storage)


def _check_for_livestreams(context: Context, channel: YoutubeChannel, statistics: '_Statistics', storage: Sqlite3Storage):
    if not context.config.monitor_livestreams:
        return

    livestream = context.api.fetch_channel_livestream(channel)
    if livestream is not None:
        if not context.livestream_recorders.is_recording_active(livestream.video_id):
            context.logger.info('new livestream "{}"'.format(livestream.title))
            livestream.filename = generate_livestream_filename(context.config.output_dir, livestream)
            context.bus.add_event(Event(type=Event.LIVESTREAM_STARTED, content=livestream))
            context.livestream_recorders.start_recording(context, livestream)
            storage.add_livestream(livestream)
        statistics.notify_active_livestream()


def _check_for_videos(context: Context,
                      channel: YoutubeChannel,
                      is_first_run: bool,
                      statistics: '_Statistics',
                      storage: Sqlite3Storage):
    for video in context.api.find_channel_uploaded_videos(channel, find_all=is_first_run):
        video_not_registered = not storage.video_exist(video.video_id) and \
                               not context.video_recorders.is_recording_active(video.video_id)
        if video_not_registered:
            context.logger.info('new video "{}"'.format(video.title))
            context.bus.add_event(Event(type=Event.NEW_VIDEO, content=video))
            if not is_first_run or context.config.archive_all:
                video.filename = generate_video_filename(context.config.output_dir, video)
                context.video_recorders.start_recording(context, video)
            storage.add_video(video)
        statistics.notify_video(new=video_not_registered)


def _process_events(context: Context, is_first_run: bool):
    try:
        for event in context.bus.retrieve_events():
            context.plugins.on_event(event, is_first_run)
    except Exception:
        context.logger.exception('exception in plugin')


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
