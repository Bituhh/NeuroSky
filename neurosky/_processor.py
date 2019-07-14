#!/usr/bin/env python3

from neurosky._connector import Connector
import threading
import os
from time import time
import numpy as np
from rx.subject import Subject
from rx.operators import take_until_with_time


class Processor(object):
    def __init__(self):  # type: (Processor) -> None
        # Editable params
        self.data_resolution = 250
        self.blink_threshold = 150
        self.recorded_data = []
        self.is_recording = False

        # Disposal handler
        self.subscriptions = []

        # Observers and Subjects
        self.data = Subject()
        self.subscriptions.append(self.data)

        # Hidden params
        self._raw_data_batch = []
        self._save_path = ''

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
                self.blink_threshold > np.amax(temp_data_batch) or -self.blink_threshold < np.amin(temp_data_batch)):
            x_fft = np.fft.rfftfreq(batch_size, 2 * (1 / fs))[2:50]
            y_fft = np.absolute(np.real(np.fft.rfft(temp_data_batch)))[2:50]
            self.data.on_next(np.array([x_fft, y_fft]))

    def record(self, path='./processor_data', recording_length=10):
        if not self.is_recording:
            self._save_path = os.path.realpath(path)
            self.recorded_data = []
            self.is_recording = True
            self.data.pipe(take_until_with_time(recording_length)).subscribe(
                observer=lambda value: self.recorded_data.append(value),
                on_error=lambda e: print(e),
                on_completed=self._save
            )
        else:
            print('Already recording...')

    def _save(self):
        np.save(self._save_path, self.recorded_data)
        self.is_recording = False
        print('Recording Complete')

    def close(self):
        print('Closing Processor...')
        for subscription in self.subscriptions:
            subscription.dispose()
        print('Processor Closed!')


if __name__ == '__main__':
    connector = Connector(debug=True, verbose=False)
    processor = Processor()
    connector.data.subscribe(processor.add_data)
    processor.data.subscribe(lambda value: print(value))
    counter = 0
    while counter < 1000:
        counter += 1
    connector.close()
    processor.close()
