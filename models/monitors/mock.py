from models.monitors.monitor import MonitorModel
from models.monitors.pagination import PAGE_SIZE
from github import Event

import uuid

class MockEvent():
    def __init__(self, id):
        self.id = id 
        self.type = 'PushEvent'
        self.commits = [{
            'sha': uuid.uuid4().hex
        }]


class MockMonitor(MonitorModel):
    def __init__(self):
        self.poll_count = 0
        self.pages = {}
        for i in range(10):
            self.pages[i] = [MockEvent(j) for j in range(PAGE_SIZE)]
    
    def poll(self):
        self.poll_count += 1

