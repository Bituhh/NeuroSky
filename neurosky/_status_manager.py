import os
from winsound import Beep
from typing import Any

from rx.subject import Subject


class StatusManager:
    def __init__(self):
        self._identifiers = []

        # Subjects
        self.status = Subject()

        # Managing Subscriptions
        self._subscriptions = []
        self._subscriptions.append(self.status)

    def add_identifier(self, identifier_name):  # type: (StatusManager, Any) -> Any
        identifier = {
            'name': identifier_name,
            'target': len(self._identifiers),
            'label_index': int(len(os.listdir('./motor_imagery_data')) / 2),
        }
        self._identifiers.append(identifier)
        return identifier

    def next_label(self, identifier):  # type: (StatusManager, Any) -> Any
        for _identifier in self._identifiers:
            if identifier['name'] is _identifier['name']:
                identifier['label_index'] += 1
                _identifier = identifier
                return _identifier['name'] + '_' + str(_identifier['label_index'])

    def update_status(self, new_status):
        self.status.on_next(new_status)

    def predicted_identifier(self, prediction):
        count = 0
        for _identifier in self._identifiers:
            if _identifier['target'] == prediction:
                if _identifier['name'] == 'right_arm':
                    Beep(500, 100)
                    count += 1
                else:
                    Beep(1000, 100)
                    count += 1
                print(_identifier['name'])
        print(count)

    def close(self):  # type: (StatusManager) -> None
        for subscription in self._subscriptions:
            subscription.dispose()
