import toml
import logging

from os import environ

from detectors import AvailableDetectors
from notifiers import Registry
from models.monitors import User, Organization, Repository


class WatcherConfig:
    def __init__(self):
        self._config = {}
        self.access_token = ''
        self.monitors = []
        self.detectors = []
        self.notifiers = []
        self.webhook = {}

    def load_file(self, filepath):
        self._config = toml.load(filepath)

        self.access_token = self._config['auth']['access_token']
        if self.access_token == 'env':
            self.access_token = environ.get('GITHUB_WATCHER_TOKEN')

        self.webhook = self._config['webhook']

        for detector in self._config['detectors']:
            if detector not in AvailableDetectors:
                logging.error(f'Unknown detector {detector} listed in configuration')
                continue
            logging.info(f'Setting up detector: {detector}')
            # TODO: Add support for per-detector configuration
            self.detectors.append(AvailableDetectors[detector]())

        for notifier_type, config in self._config['notifiers'].items():
            notifier = Registry.get(notifier_type)
            if not notifier:
                logging.error(f'Invalid notifier type: {notifier_type}')
                continue
            logging.info(f'Setting up notifier: {notifier_type}')
            self.notifiers.append(notifier(config))

        self.validate()

    def create_monitors(self, client):
        for organization in self._config['monitors'].get('organizations', []):
            logging.info(f'Monitoring organization: {organization}')
            self.monitors.append(Organization(organization, client))
        for user in self._config['monitors'].get('users', []):
            logging.info(f'Monitoring user: {user}')
            self.monitors.append(User(user, client))
        for repository in self._config['monitors'].get('repos', []):
            logging.info(f'Monitoring repository: {repository}')
            self.monitors.append(Repository(repository, client))

    def validate(self):
        if not self.access_token:
            raise Exception('No access token specified')
        if not self.detectors:
            raise Exception('No detectors provided')


Config = WatcherConfig()
