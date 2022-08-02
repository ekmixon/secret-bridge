import logging
import requests

from constants import PUSH_EVENT_TYPE
from processor import Processor

DEFAULT_RETRY_COUNT = 5


class Poller:
    """A helper responsible for managing the event polling for different
    monitors, such as organizations, repositories, and developers.
    """
    def __init__(self,
                 monitors,
                 event_types=[PUSH_EVENT_TYPE],
                 retries=DEFAULT_RETRY_COUNT):
        if not event_types:
            event_types = [PUSH_EVENT_TYPE]
        self.monitors = monitors
        self.event_types = event_types
        self.retry_count = retries

    def _poll_with_retry(self, monitor):
        attempts = 0
        while True:
            attempts += 1
            try:
                return monitor.poll()
            except requests.exceptions.ConnectionError as e:
                if attempts > self.retry_count:
                    raise e
                logging.warn(
                    f'ConnectionError when requesting events... attempt {attempts}/{self.retry_count}'
                )

    def poll(self):
        events = {}
        for monitor in self.monitors:
            results = self._poll_with_retry(monitor)
            logging.debug('{} events fetched')
            for result in results:
                if result.type not in self.event_types:
                    logging.debug(
                        f'Found invalid event type: Event ID {result.id} with type {result.type}'
                    )

                    continue
                events[result.id] = result
                logging.debug(f'Found PushEvent {result.id}')
        for _, event in events.items():
            Processor.process_event(event)
