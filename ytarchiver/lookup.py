from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ytarchiver.download import download
from ytarchiver.storage import open_storage, Entry

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def create_service(config, logger):
    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=config.api_key,
        cache_discovery=False
    )


def lookup(config, logger, service, first_run):
    total_videos = 0
    new_videos = 0

    with open_storage(config.output_dir) as s:
        for channel_id in config.channels_list:
            try:
                for upload in _fetch_uploaded_videos(service, channel_id):
                    video_id = upload['resourceId']['videoId']
                    if not s.exist(video_id):
                        entry = Entry(
                            video_id=video_id,
                            channel_id=upload['channelId'],
                            timestamp=upload['publishedAt'],
                            title=upload['title'],
                            channel_name=upload['channelTitle']
                        )

                        logger.info('new video "{}"'.format(entry.title))

                        do_download = False
                        if not first_run or config.archive_all:
                            do_download = True
                            file_path = download(config, logger, entry)
                            entry.filename = file_path

                        s.add(entry)
                        if do_download:
                            s.commit()
                        new_videos += 1
                    total_videos += 1
            except HttpError as e:
                logger.error(e)
                return
            finally:
                s.commit()

    logger.info('total videos: {}, new: {}'.format(total_videos, new_videos))


def _fetch_uploaded_videos(service, channel_id):
    results = service.channels().list(
        part="snippet,contentDetails",
        id=channel_id
    ).execute()

    for channel in results['items']:
        uploads_playlist_id = channel['contentDetails']['relatedPlaylists']['uploads']
        next_page_token = ''

        while next_page_token is not None:
            playlistitems_response = service.playlistItems().list(
                playlistId=uploads_playlist_id,
                part='snippet',
                maxResults=50,
                pageToken=next_page_token
            ).execute()

            for playlist_item in playlistitems_response['items']:
                yield playlist_item['snippet']

            next_page_token = playlistitems_response.get('nextPageToken')
