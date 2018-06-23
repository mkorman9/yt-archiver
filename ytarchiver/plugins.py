import logging

import yaml
import requests

from ytarchiver.common import PluginsManager, Plugin, Event


class HttpPlugin(Plugin):
    """
    HttpPlugin send HTTP request every time new video or new livestream is fetched from one of monitored channels.
    By default it skips videos that are already uploaded before application is started.
    """

    DEFAULT_TIMEOUT = 5

    def __init__(self, config):
        self._config = config
        self._timeout = HttpPlugin.DEFAULT_TIMEOUT

        if 'url' not in self._config:
            raise Exception('missing required parameter "url" for http plugin')
        if 'timeout' in self._config:
            self._timeout = int(self._config['timeout'])

    def on_event(self, event: Event, is_first_run: bool):
        if is_first_run:
            return

        payload = {
            'event_type': self._translate_event_type(event.type),
            'data': {
                'title': event.content.title,
                'video_id': event.content.video_id,
                'timestamp': event.content.timestamp,
                'channel_id': event.content.channel_id,
                'channel_name': event.content.channel_name
            }
        }

        requests.post(
            self._config['url'],
            json=payload,
            timeout=self._timeout
        )

    def _translate_event_type(self, event_type: int) -> str:
        if event_type == Event.NEW_VIDEO:
            return 'new_video'
        elif event_type == Event.VIDEO_DOWNLOADED:
            return 'video_downloaded'
        elif event_type == Event.LIVESTREAM_STARTED:
            return 'livestream_started'
        elif event_type == Event.LIVESTREAM_INTERRUPTED:
            return 'livestream_interrupted'


PLUGINS = {
    'http': HttpPlugin
}


class ParsingError(Exception):
    """
    Exception raised on configuration file parsing
    """

    def __init__(self, message: str):
        super(ParsingError, self).__init__(message)


def load_plugins_configuration(path: str, plugins_manager: PluginsManager, logger: logging.Logger):
    """
    Load plugins configuration from YAML file

    :param path: path to configuration file
    :param plugins_manager: instance of PluginsManager
    :param logger: instance of Logger
    """

    try:
        with open(path, 'r') as f:
            document = yaml.load(f)
            if document is None:
                raise ParsingError('malformed YAML document')
            if 'plugins' not in document.keys():
                raise ParsingError('missing "plugins" section')

            for plugin in document['plugins']:
                if 'name' not in plugin.keys():
                    raise ParsingError('missing "name" section in one of plugins')

                plugin_name = plugin['name'].lower()
                plugin_config = plugin.get('config', None)

                if plugin_name not in PLUGINS:
                    raise ParsingError('unknown plugin "{}"'.format(plugin_name))

                try:
                    logger.info('registering plugin "{}"'.format(plugin_name))
                    plugin = PLUGINS[plugin_name](plugin_config)
                    plugins_manager.register_plugin(plugin)
                except Exception:
                    logger.exception('error while initialising plugin "{}"'.format(plugin_name))

    except IOError:
        logger.exception('error while loading plugins configuration file; skipping plugins setup')
    except (yaml.YAMLError, ParsingError):
        logger.exception('error while parsing plugins configuration file; skipping plugins setup')
