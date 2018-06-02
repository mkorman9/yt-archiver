from datetime import datetime


class Context:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.service = None


class Video:
    def __init__(self,
                 video_id: str,
                 channel_id: str,
                 timestamp: datetime,
                 title: str,
                 channel_name: str,
                 filename: str=None):
        self.video_id = video_id
        self.channel_id = channel_id
        self.timestamp = timestamp
        self.title = title
        self.channel_name = channel_name
        self.filename = filename

    def __str__(self):
        return '{}\t{}\t{}\t{}\t{}\t{}'.format(
            self.video_id,
            self.channel_id,
            self.timestamp,
            self.title,
            self.channel_name,
            self.filename
        )

    def __repr__(self):
        return self.__str__()


