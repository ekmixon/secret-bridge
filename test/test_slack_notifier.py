import unittest
from unittest.mock import patch
from pathlib import Path
from os import environ
from config import Config
from notifiers import Registry
from notifiers.slack import SlackWebhookNotifier
from models.finding import Finding


class TestSlackIntegration(unittest.TestCase):
    @patch('requests.post')
    def test_webhook_url(self, mock_post):
        environ['GITHUB_WATCHER_TOKEN'] = 'abcdef'
        notifier = next(
            (n for n in Config.notifiers if isinstance(n, SlackWebhookNotifier)),
            None,
        )

        findings = [
            Finding("testfile.py", 123, "test_secret_type",
                    "https://www.example.com")
        ]
        notifier.process(findings, 'test-detector')


if __name__ == "__main__":
    unittest.main()
