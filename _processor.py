#!/usr/bin/env python3

from _connector import Connector
import threading
from numpy import amin, amax, fft, absolute, real, array
from rx.subjects import Subject


class Processor(object):
    def __init__(self):  # type: (Processor) -> None
        # Editable params
        self.data_resolution = 250
        self.blink_threshold = 150

        # Disposal handler
        self.subscriptions = []

        # Observers and Subjects
        self.data = Subject()
        self.subscriptions.append(self.data)

        # Hidden params
        self._raw_data_batch = []

    @staticmethod
    def _init_thread(target, args=()):  # type: (Any, Union[Tuple, Any]) -> None
        threading.Thread(target=target, args=args).start()

    def add_data(self, raw_data):  # type: (Processor, int) -> None
        self._raw_data_batch.append(raw_data)
        if len(self._raw_data_batch) >= self.data_resolution:
            self._init_thread(target=self._fft)

    def _fft(self):  # type: (Processor) -> None
        temp_data_batch = self._raw_data_batch.copy()
        self._raw_data_batch = []
        batch_size = len(temp_data_batch)
        fs = 512
        if batch_size is not 0 and (
                self.blink_threshold > amax(temp_data_batch) or -self.blink_threshold < amin(temp_data_batch)):
            x_fft = fft.rfftfreq(batch_size, 2 * (1 / fs))[2:50]
            y_fft = absolute(real(fft.rfft(temp_data_batch)))[2:50]
            self.data.on_next(array([x_fft, y_fft]))

    def close(self):
        for subscription in self.subscriptions:
            subscription.dispose()


if __name__ == '__main__':
    connector = Connector(debug=True, verbose=False)
    processor = Processor()
    connector.data.subscribe(lambda data: processor.add_data(data))
    processor.data.subscribe(lambda value: print(value))
    counter = 0
    while counter < 1000:
        counter += 1
    connector.close()
    processor.close()
