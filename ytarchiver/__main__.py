import logging
import sys
import os
import errno
import time

from datetime import datetime

from ytarchiver.args import parse_command_line
from ytarchiver.lookup import create_service, lookup
from ytarchiver.storage import get_saved_entries


def main():
    config = parse_command_line()
    logger = create_logger()

    if config.do_list:
        list_entries(config, logger)
    else:
        start_listening(config, logger)


def create_logger():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format='%(message)s')
    logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
    logger = logging.getLogger('ytarchiver')
    return logger


def list_entries(config, logger):
    logger.info('Video ID\tChannel ID\tTimestamp\tTitle\tChannel Name\tFilename')
    for entry in get_saved_entries(config, logger):
        logger.info(entry)


def start_listening(config, logger):
    ensure_dir_exist(config.output_dir, logger)
    verify_channels_list_not_empty(config, logger)

    service = create_service(config, logger)

    logger.debug('daemon started successfully')

    _trigger_lookup(config, logger, service, first_run=True)

    try:
        while True:
            time.sleep(config.refresh_time)
            _trigger_lookup(config, logger, service)
    except KeyboardInterrupt:
        logger.debug('interrupted with ctrl+c')


def _trigger_lookup(config, logger, service, first_run=False):
    now = datetime.now()
    logger.debug('[{}] triggering new lookup...'.format(now.strftime('%Y-%m-%d %H:%M:%S')))
    lookup(config, logger, service, first_run)


def ensure_dir_exist(path, logger):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            logger.error(e)
            sys.exit(1)


def verify_channels_list_not_empty(config, logger):
    if len(config.channels_list) == 0:
        logger.error('channels list cannot be empty, use -m option to specify at least one channel id')
        sys.exit(1)


if __name__ == '__main__':
    main()
