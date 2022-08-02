from notifiers.notifier import Notifier
from notifiers import Registry

class ConsoleNotifier(Notifier):
    notifier_id = 'console'

    def __init__(self, config):
        super()

    def process(self, findings, detector_name):
        """Print the findings to the console with a heading for the detector name."""
        print(f"{detector_name} found the following:")
        for finding in findings:
            print(finding)


Registry.register(ConsoleNotifier.notifier_id, ConsoleNotifier)
