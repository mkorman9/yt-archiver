import os
from pytube import YouTube
from pytube.helpers import safe_filename


YOUTUBE_URL_PREFIX = 'https://www.youtube.com/watch?v='


def download_stream(config, logger):
    pass


def download_video(context, video):
    download_link = YOUTUBE_URL_PREFIX + video.video_id
    total_size = 0

    def on_progress(stream, chunk, handle, bytes_remaining):
        context.logger.debug('downloading... {}/{}'.format(total_size - bytes_remaining, total_size))

    def on_complete(stream, handle):
        context.logger.debug('download complete')

    yt = YouTube(download_link)
    yt.register_on_complete_callback(on_complete)
    yt.register_on_progress_callback(on_progress)
    streams = yt.streams.all()
    stream = _choose_best_stream(streams)
    total_size = stream.filesize
    filename = safe_filename(video.timestamp + ' ' + video.title)

    context.logger.info('downloading "{}"'.format(video.title))
    stream.download(
        output_path=context.config.output_dir,
        filename=filename
    )

    return os.path.join(context.config.output_dir, '{}.{}'.format(filename, stream.subtype))


def _choose_best_stream(streams):
    best_stream = None
    for stream in streams:
        if stream.includes_audio_track and stream.includes_video_track:
            if best_stream is None:
                best_stream = stream

            higher_resolution = stream.resolution > best_stream.resolution
            equal_resolution = stream.resolution == best_stream.resolution
            better_format = 'mp4' in stream.mime_type and 'mp4' not in best_stream.mime_type
            if better_format and (equal_resolution or higher_resolution):
                best_stream = stream
            if higher_resolution:
                best_stream = stream

    return best_stream
