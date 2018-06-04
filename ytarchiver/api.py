from typing import Iterator, Optional, List, Any, Tuple

from googleapiclient.discovery import build

from ytarchiver.common import Context, ContentItem

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def prepare_context(context: Context):
    context.service = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=context.config.api_key,
        cache_discovery=False
    )


def find_channels_list(context: Context) -> List[Tuple[str, Any]]:
    retrieved_channels = []
    request_for = ','.join(context.config.channels_list)

    results = context.service.channels().list(
        part="snippet,contentDetails",
        id=request_for
    ).execute()

    for data in results['items']:
        retrieved_channels.append((data['id'], data['contentDetails']))

    return retrieved_channels


def fetch_channel_livestream(context: Context, channel_id: str) -> Optional[ContentItem]:
    live_streams = context.service.search().list(
        part="id,snippet",
        channelId=channel_id,
        type='video',
        eventType='live'
    ).execute()

    for stream in live_streams['items']:
        return ContentItem(
            video_id=stream['id']['videoId'],
            channel_id=channel_id,
            timestamp=stream['snippet']['publishedAt'],
            title=stream['snippet']['title'],
            channel_name=stream['snippet']['channelTitle']
        )

    return None


def find_channel_uploaded_videos(context: Context, channel_content: Any, is_first_run: bool=False) -> Iterator[ContentItem]:
    uploads_playlist_id = channel_content['relatedPlaylists']['uploads']
    next_page_token = ''

    while next_page_token is not None:
        playlistitems_response = context.service.playlistItems().list(
            playlistId=uploads_playlist_id,
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

        next_page_token = playlistitems_response.get('nextPageToken') if is_first_run else None
