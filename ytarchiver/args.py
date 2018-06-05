import argparse

DEFAULT_REFRESH_TIME_SEC = 5 * 60  # 5 min
DEFAULT_OUTPUT_DIRECTORY = './out'
DEFAULT_ARCHIVE_ALL = False
DEFAULT_MONITOR_LIVESTREAMS = False


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t', '--time',
        dest='refresh_time',
        help='time between consecutive lookups for videos (in seconds)',
        default=DEFAULT_REFRESH_TIME_SEC,
        type=int
    )
    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        help='directory to store videos and the database, default: ' + DEFAULT_OUTPUT_DIRECTORY,
        default=DEFAULT_OUTPUT_DIRECTORY,
        type=str
    )
    parser.add_argument(
        '-a', '--all',
        dest='archive_all',
        help='archive all videos from past, default action is to save only new videos',
        default=DEFAULT_ARCHIVE_ALL,
        action='store_true'
    )
    parser.add_argument(
        '-s', '--streams',
        dest='monitor_livestreams',
        help='also monitor active livestreams and record all of them',
        default=DEFAULT_MONITOR_LIVESTREAMS,
        action='store_true'
    )
    parser.add_argument(
        '-k', '--key',
        dest='api_key',
        help='Google API key',
        default=None,
        type=str
    )
    parser.add_argument(
        '-m', '--monitor',
        dest='channels_list',
        help='list of channels to monitor, use channel IDs split by space such as: UC8e8Ag9Or9ra4J6jl4qjfEg ...',
        nargs='+',
        default=[]
    )

    config = parser.parse_args()
    return config
