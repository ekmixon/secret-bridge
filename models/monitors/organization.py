import logging

from state import State
from models.monitors.monitor import MonitorModel
from models.monitors.pagination import paginate


class Organization(MonitorModel):
    def __init__(self, organization_name, client):
        self.name = organization_name
        self.event_offset = 0
        if stored_offset := State.get('organization', self.name):
            self.event_offset = stored_offset
        self.client = client
        self.organization = client.get_organization(self.name)

    def poll(self):
        events = paginate(self.organization.get_events,
                          event_offset=self.event_offset)
        if events:
            logging.info(f'Found {len(events)} events for organization {self.name}')
            self.event_offset = int(events[0].id)
            State.update('organization', self.name, self.event_offset)
        return events
