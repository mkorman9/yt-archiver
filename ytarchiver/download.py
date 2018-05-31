import os
from pytube import YouTube

VIDEO_DOWNLOAD_PREFIX = 'https://www.youtube.com/watch?v='


def download(config, logger, entry):
    download_link = VIDEO_DOWNLOAD_PREFIX + entry.video_id
    total_size = 0

    def on_progress(stream, chunk, handle, bytes_remaining):
        logger.debug('downloading... {}/{}'.format(total_size - bytes_remaining, total_size))

    def on_complete(stream, handle):
        logger.debug('download complete')

    yt = YouTube(download_link)
    yt.register_on_complete_callback(on_complete)
    yt.register_on_progress_callback(on_progress)
    streams = yt.streams.all()
    stream = _choose_best_stream(streams)
    total_size = stream.filesize
    filename = entry.timestamp + ' ' + entry.title

    logger.info('downloading "{}"'.format(entry.title))
    stream.download(
        output_path=config.output_dir,
        filename=filename
    )

    return os.path.join(config.output_dir, '{}.{}'.format(filename, stream.subtype))


def _choose_best_stream(streams):
    best_stream = None
    for stream in streams:
        if stream.includes_audio_track and stream.includes_video_track:
            if best_stream is None:
                best_stream = stream

            if 'mp4' in stream.mime_type and 'mp4' not in best_stream.mime_type:
                best_stream = stream
    return best_stream
