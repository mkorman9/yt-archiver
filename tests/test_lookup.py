import logging
from unittest import TestCase

from datetime import datetime
from mock import MagicMock, create_autospec

from ytarchiver.api import YoutubeAPI, YoutubeChannel
from ytarchiver.common import Context, RecordersController, StorageManager, ContentItem
from ytarchiver.lookup import lookup


class LookupTest(TestCase):
    def test_lookup_flow_first_run(self):
        # given
        context = self._create_context()

        # when
        lookup(context, is_first_run=True)

        # then
        # TODO

    def _create_context(self):
        config = MagicMock()
        logger = create_autospec(logging.Logger)
        api = create_autospec(YoutubeAPI)
        video_recorders_controller = create_autospec(RecordersController)
        livestream_recorders_controller = create_autospec(RecordersController)
        storage_manager = create_autospec(StorageManager)

        api.find_channels.return_value = [
            YoutubeChannel('id1', {'relatedPlaylists': {'uploads': 'uploads_playlistid1'}}),
            YoutubeChannel('id2', {'relatedPlaylists': {'uploads': 'uploads_playlistid2'}})
        ]
        api.find_channel_uploaded_videos.side_effect = lambda channel, find_all: [
            ContentItem(
                video_id='video1',
                channel_id=channel.id,
                timestamp=datetime.utcnow(),
                title='video #1',
                channel_name='channel ' + channel.id
            ),
            ContentItem(
                video_id='video2',
                channel_id=channel.id,
                timestamp=datetime.utcnow(),
                title='video #2',
                channel_name='channel ' + channel.id
            )
        ]
        api.fetch_channel_livestream.side_effect = lambda channel: ContentItem(
            video_id='livestream',
            channel_id=channel.id,
            timestamp=datetime.utcnow(),
            title='livestream #live',
            channel_name='channel ' + channel.id
        )

        return Context(
            config,
            logger,
            api=api,
            video_recorders_controller=video_recorders_controller,
            livestream_recorders_controller=livestream_recorders_controller,
            storage_manager=storage_manager
        )
