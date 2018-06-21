import logging
from datetime import datetime
from unittest import TestCase

from mock import MagicMock, create_autospec, call

from ytarchiver.api import YoutubeAPI, YoutubeChannel
from ytarchiver.common import Context, RecordersController, StorageManager, ContentItem
from ytarchiver.lookup import lookup


CHANNEL_1 = YoutubeChannel('id1', {'relatedPlaylists': {'uploads': 'uploads_playlistid1'}})
VIDEO_1 = ContentItem(
    video_id='video1',
    channel_id='channel_id',
    timestamp=datetime.utcnow(),
    title='video #1',
    channel_name='some channel'
)
VIDEO_2 = ContentItem(
    video_id='video2',
    channel_id='channel_id',
    timestamp=datetime.utcnow(),
    title='video #2',
    channel_name='some channel'
)
LIVESTREAM_1 = ContentItem(
    video_id='livestream',
    channel_id='channel_id',
    timestamp=datetime.utcnow(),
    title='livestream #live',
    channel_name='some channel'
)


class LookupTest(TestCase):
    def test_should_search_for_videos_and_save_results(self):
        # given
        context, storage = _create_context_and_storage()

        context.config.archive_all = False
        context.config.monitor_livestreams = False

        storage.video_exist.return_value = False

        context.video_recorders.is_recording_active.return_value = False
        context.livestream_recorders.is_recording_active.return_value = False

        context.api.find_channels.return_value = [CHANNEL_1]
        context.api.find_channel_uploaded_videos.return_value = [VIDEO_1, VIDEO_2]

        # when
        lookup(context, is_first_run=True)

        # then
        storage.add_video.assert_has_calls([
            call(context.api.find_channel_uploaded_videos.return_value[0]),
            call(context.api.find_channel_uploaded_videos.return_value[1])
        ], any_order=True)
        storage.add_livestream.assert_not_called()
        context.livestream_recorders.start_recording.assert_not_called()
        context.video_recorders.start_recording.assert_not_called()
        storage.commit.assert_called()

    def test_should_search_for_all_content_and_save_results_and_start_recording_livestream(self):
        # given
        context, storage = _create_context_and_storage()

        context.config.archive_all = False
        context.config.monitor_livestreams = True

        storage.video_exist.return_value = False

        context.video_recorders.is_recording_active.return_value = False
        context.livestream_recorders.is_recording_active.return_value = False

        context.api.find_channels.return_value = [CHANNEL_1]
        context.api.find_channel_uploaded_videos.return_value = [VIDEO_1, VIDEO_2]
        context.api.fetch_channel_livestream.return_value = LIVESTREAM_1

        # when
        lookup(context, is_first_run=True)

        # then
        storage.add_video.assert_has_calls([
            call(context.api.find_channel_uploaded_videos.return_value[0]),
            call(context.api.find_channel_uploaded_videos.return_value[1])
        ], any_order=True)
        storage.add_livestream.assert_has_calls([
            call(context.api.fetch_channel_livestream.return_value)
        ], any_order=True)
        context.livestream_recorders.start_recording.assert_has_calls([
            call(context, context.api.fetch_channel_livestream.return_value)
        ], any_order=True)
        context.video_recorders.start_recording.assert_not_called()
        storage.commit.assert_called()

    def test_should_search_for_videos_and_archive_all(self):
        # given
        context, storage = _create_context_and_storage()

        context.config.archive_all = True
        context.config.monitor_livestreams = False

        storage.video_exist.return_value = False

        context.video_recorders.is_recording_active.return_value = False
        context.livestream_recorders.is_recording_active.return_value = False

        context.api.find_channels.return_value = [CHANNEL_1]
        context.api.find_channel_uploaded_videos.return_value = [VIDEO_1, VIDEO_2]

        # when
        lookup(context, is_first_run=True)

        # then
        storage.add_video.assert_has_calls([
            call(context.api.find_channel_uploaded_videos.return_value[0]),
            call(context.api.find_channel_uploaded_videos.return_value[1])
        ], any_order=True)
        storage.add_livestream.assert_not_called()
        context.video_recorders.start_recording.assert_has_calls([
            call(context, context.api.find_channel_uploaded_videos.return_value[0]),
            call(context, context.api.find_channel_uploaded_videos.return_value[1])
        ], any_order=True)
        context.livestream_recorders.start_recording.assert_not_called()
        storage.commit.assert_called()

    def test_should_download_newly_fetched_videos(self):
        # given
        context, storage = _create_context_and_storage()

        context.config.archive_all = False
        context.config.monitor_livestreams = False

        storage.video_exist.return_value = False

        context.video_recorders.is_recording_active.return_value = False
        context.livestream_recorders.is_recording_active.return_value = False

        context.api.find_channels.return_value = [CHANNEL_1]
        context.api.find_channel_uploaded_videos.return_value = [VIDEO_1, VIDEO_2]

        # when
        lookup(context, is_first_run=False)

        # then
        storage.add_video.assert_has_calls([
            call(context.api.find_channel_uploaded_videos.return_value[0]),
            call(context.api.find_channel_uploaded_videos.return_value[1])
        ], any_order=True)
        storage.add_livestream.assert_not_called()
        context.video_recorders.start_recording.assert_has_calls([
            call(context, context.api.find_channel_uploaded_videos.return_value[0]),
            call(context, context.api.find_channel_uploaded_videos.return_value[1])
        ], any_order=True)
        context.livestream_recorders.start_recording.assert_not_called()
        storage.commit.assert_called()

    def test_should_not_download_if_video_already_exist(self):
        # given
        context, storage = _create_context_and_storage()

        context.config.archive_all = False
        context.config.monitor_livestreams = False

        storage.video_exist.return_value = True

        context.video_recorders.is_recording_active.return_value = False
        context.livestream_recorders.is_recording_active.return_value = False

        context.api.find_channels.return_value = [CHANNEL_1]
        context.api.find_channel_uploaded_videos.return_value = [VIDEO_1, VIDEO_2]

        # when
        lookup(context, is_first_run=False)

        # then
        storage.add_video.assert_not_called()
        storage.add_livestream.assert_not_called()
        context.video_recorders.start_recording.assert_not_called()
        context.livestream_recorders.start_recording.assert_not_called()
        storage.commit.assert_called()


def _create_context_and_storage():
    config = MagicMock()
    config.output_dir = 'fake_output_directory'
    logger = create_autospec(logging.Logger, spec_set=True)
    api = create_autospec(YoutubeAPI, spec_set=True)
    video_recorders_controller = create_autospec(RecordersController, spec_set=True)
    livestream_recorders_controller = create_autospec(RecordersController, spec_set=True)

    storage_manager = create_autospec(StorageManager, spec_set=True)
    storage_manager.open.return_value.__enter__.return_value = MagicMock()
    storage = storage_manager.open.return_value.__enter__.return_value

    context = Context(
        config,
        logger,
        api=api,
        video_recorders_controller=video_recorders_controller,
        livestream_recorders_controller=livestream_recorders_controller,
        storage_manager=storage_manager
    )
    return context, storage
