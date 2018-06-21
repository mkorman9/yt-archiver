from typing import Iterator, Optional, List, Any

from googleapiclient.discovery import build

from ytarchiver.common import ContentItem

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class YoutubeChannel:
    def __init__(self, id: str, uploads_playlist_id: str):
        self.id = id
        self.uploads_playlist_id = uploads_playlist_id


class YoutubeAPI:
    def __init__(self, key: str):
        if key is not None:
            self._service = build(
                YOUTUBE_API_SERVICE_NAME,
                YOUTUBE_API_VERSION,
                developerKey=key,
                cache_discovery=False
            )

    def find_channels(self, channels_ids_list: List[str]) -> Iterator[YoutubeChannel]:
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

    def fetch_channel_livestream(self, channel: YoutubeChannel) -> Optional[ContentItem]:
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

    def find_channel_uploaded_videos(self,
                                     channel: YoutubeChannel,
                                     find_all: bool=False) -> Iterator[ContentItem]:
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
