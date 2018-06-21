import errno
import logging
import os
import sys
import time
from datetime import datetime

from ytarchiver.api import YoutubeAPI
from ytarchiver.args import parse_command_line
from ytarchiver.common import Context
from ytarchiver.lookup import lookup
from ytarchiver.recording import MultiprocessLivestreamRecordersController, SynchronousVideoRecordersController
from ytarchiver.sqlite import Sqlite3StorageManager


def main():
    config = parse_command_line()
    logger = create_logger()
    context = Context(
        config,
        logger,
        api=YoutubeAPI(config.api_key),
        video_recorders_controller=SynchronousVideoRecordersController(),
        livestream_recorders_controller=MultiprocessLivestreamRecordersController(),
        storage_manager=Sqlite3StorageManager()
    )

    start_monitoring(context)


def create_logger():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format='%(message)s')
    logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
    logger = logging.getLogger('ytarchiver')
    return logger


def start_monitoring(context: Context):
    ensure_dir_exist(context.config.output_dir, context.logger)
    if len(context.config.channels_list) == 0:
        context.logger.error('channels list cannot be empty, use -m option to specify at least one channel id')
        sys.exit(1)

    context.logger.debug('daemon started successfully')

    try:
        _trigger_lookup(context, first_run=True)

        # master thread's loop
        while True:
            time.sleep(context.config.refresh_time)
            _trigger_lookup(context)
    except KeyboardInterrupt:
        context.logger.debug('interrupted with ctrl+c')


def _trigger_lookup(context, first_run=False):
    now = datetime.now()
    context.logger.debug('[{}] triggering new lookup...'.format(now.strftime('%Y-%m-%d %H:%M:%S')))
    lookup(context, first_run)


def ensure_dir_exist(path: str, logger: logging.Logger):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            logger.error(e)
            sys.exit(1)


if __name__ == '__main__':
    main()
