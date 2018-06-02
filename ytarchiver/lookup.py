from googleapiclient.errors import HttpError

from ytarchiver.api import find_channel_uploaded_videos, fetch_channel_livestream
from ytarchiver.download import download_video
from ytarchiver.storage import open_storage


class Statistics:
    def __init__(self):
        self.total_videos = 0
        self.new_videos = 0
        self.active_livestreams = 0

    def notify_video(self, new=False):
        self.total_videos += 1
        if new:
            self.new_videos += 1

    def notify_active_livestream(self):
        self.active_livestreams += 1


def lookup(context, is_first_run):
    statistics = Statistics()

    with open_storage(context.config.output_dir) as storage:
        for channel_id in context.config.channels_list:
            _fetch_channel_content(context, channel_id, storage, statistics, is_first_run)

    context.logger.info(
        'total videos: {}, new: {}, livestream {}'.format(
            statistics.total_videos,
            statistics.new_videos,
            statistics.active_livestreams
        )
    )


def _fetch_channel_content(context, channel_id, storage, statistics, is_first_run=False):
    try:
        if fetch_channel_livestream(context, channel_id):
            statistics.notify_active_livestream()

        for video in find_channel_uploaded_videos(context, channel_id):
            video_not_registered = not storage.video_exist(video.video_id)
            if video_not_registered:
                _register_video(context, storage, video, is_first_run)
            statistics.notify_video(new=video_not_registered)
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


def _register_video(context, storage, video, first_run):
    should_be_downloaded = not first_run or context.config.archive_all

    context.logger.info('new video "{}"'.format(video.title))

    if should_be_downloaded:
        file_path = download_video(context, video)
        video.filename = file_path

    storage.add_video(video)

    if should_be_downloaded:
        storage.commit()
