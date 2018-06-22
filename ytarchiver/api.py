from typing import Iterator, Optional, List

from googleapiclient.discovery import build

from ytarchiver.common import ContentItem

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class APIError(Exception):
    """
    Error caused by API call
    """

    def __init__(self, cause):
        super(APIError, self).__init__(cause)


class YoutubeChannel:
    """
    Representation of Youtube channel and associated data
    """
    def __init__(self, id: str, uploads_playlist_id: str):
        self.id = id
        self.uploads_playlist_id = uploads_playlist_id


class YoutubeAPI:
    """
    Object allowing to make API calls
    """
    def __init__(self, key: str):
        if key is not None:
            self._service = build(
                YOUTUBE_API_SERVICE_NAME,
                YOUTUBE_API_VERSION,
                developerKey=key,
                cache_discovery=False
            )

    def find_channels(self, channels_ids_list: List[str]) -> Iterator[YoutubeChannel]:
        """
        Returns channels represented by given ids

        :param channels_ids_list: IDs of channels
        :return: channels data
        :exception APIError
        """
        try:
            request_for = ','.join(channels_ids_list)

            results = self._service.channels().list(
                part="snippet,contentDetails",
                id=request_for
            ).execute()

            for data in results['items']:
                yield YoutubeChannel(
                    data['id'],
                    data['contentDetails']['relatedPlaylists']['uploads']
                )
        except Exception as e:
            raise APIError(e)

    def fetch_channel_livestream(self, channel: YoutubeChannel) -> Optional[ContentItem]:
        """
        Returns livestream's data if it is currently active, or None otherwise

        :param channel: channel to check
        :return: livestream's data or None
        :exception APIError
        """
        try:
            live_streams = self._service.search().list(
                part="id,snippet",
                channelId=channel.id,
                type='video',
                eventType='live'
            ).execute()

            for stream in live_streams['items']:
                return ContentItem(
                    video_id=stream['id']['videoId'],
                    channel_id=channel.id,
                    timestamp=stream['snippet']['publishedAt'],
                    title=stream['snippet']['title'],
                    channel_name=stream['snippet']['channelTitle']
                )

            return None
        except Exception as e:
            raise APIError(e)

    def find_channel_uploaded_videos(self,
                                     channel: YoutubeChannel,
                                     find_all: bool=False) -> Iterator[ContentItem]:
        """
        Returns videos uploaded from given channel.

        :param channel: channel to check
        :param find_all: if it is False - only the first 50 videos are fetched
        :return: videos
        :exception APIError
        """
        try:
            next_page_token = ''

            while next_page_token is not None:
                playlistitems_response = self._service.playlistItems().list(
                    playlistId=channel.uploads_playlist_id,
                    part='snippet',
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()

                for playlist_item in playlistitems_response['items']:
                    upload = playlist_item['snippet']
                    yield ContentItem(
                        video_id=upload['resourceId']['videoId'],
                        channel_id=upload['channelId'],
                        timestamp=upload['publishedAt'],
                        title=upload['title'],
                        channel_name=upload['channelTitle']
                    )

                next_page_token = playlistitems_response.get('nextPageToken') if find_all else None
        except Exception as e:
            raise APIError(e)
