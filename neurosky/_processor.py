#!/usr/bin/env python3

import threading
import os
import numpy as np
from rx.internal import DisposedException
from sklearn.decomposition import PCA
from sklearn.decomposition import FastICA

try:
    from neurosky._connector import Connector
except ModuleNotFoundError:
    from _connector import Connector
from time import sleep
from rx.subject import Subject
from rx.operators import take_until_with_time


class Processor(object):
    def __init__(self, batch_mode=False, live=False):  # type: (Processor, bool) -> None
        # Editable params
        self._is_live_recording = live
        self.data_resolution = 250
        self.blink_threshold = 50000000
        self.recorded_data = []
        self.is_recording = False
        self._is_open = True
        self._sample_frequency = 512
        self.batch_mode = batch_mode
        self.processed_data = []

        # Disposal handler
        self.subscriptions = []

        # Observers and Subjects
        self.data = Subject()
        self.subscriptions.append(self.data)

        # Hidden params
        self._raw_data_batch = []
        self._save_path = ''

        split = 50

        self._pca = PCA(
            n_components=split,
            whiten=False,
            # iterated_power=100
            # random_state=5
        )
        self._ica = FastICA(
            n_components=split,
            # whiten=False,
            # max_iter=1000,
            tol=1
        )

    @staticmethod
    def _init_thread(target, args=()):  # type: (Any, Union[Tuple, Any]) -> None
        threading.Thread(target=target, args=args).start()

    def add_data(self, raw_data):  # type: (Processor, int) -> None
        if not self.batch_mode:
            self._raw_data_batch.append(raw_data)
            if len(self._raw_data_batch) >= self.data_resolution and self._is_open:
                self._init_thread(target=self._fft)

    def fft(self, data_batch):
        if self.batch_mode:
            for data in data_batch:
                self._raw_data_batch.append(data)
            self._fft()

    def set_sampling_rate(self, fs):
        self._sample_frequency = fs

    def _fft(self):  # type: (Processor) -> None
        temp_data_batch = self._raw_data_batch.copy()
        self._raw_data_batch = []
        batch_size = len(temp_data_batch)
        print(batch_size)
        if batch_size is not 0 and (
                self.blink_threshold > np.amax(temp_data_batch) or -self.blink_threshold < np.amin(temp_data_batch)):
            x_fft = np.fft.rfftfreq(batch_size, 2 * (1 / self._sample_frequency))
            if self._is_live_recording:
                slice_size = 48
            else:
                slice_size = round(len(list(filter(lambda x: x < 50, x_fft))), -1)
            # slice_size = 100
            x_fft = x_fft[:slice_size]
            # print(max(x_fft))
            y_fft = np.absolute(np.real(np.fft.rfft(temp_data_batch)))[:slice_size]
            # print(len(y_fft))
            self.processed_data = np.array([x_fft, y_fft])[1]
            self.data.on_next(self.processed_data)

    def pca(self, X):
        X = (X - np.mean(X, axis=0)) / np.std(X, axis=0)
        # print(X.shape)
        a = self._pca.fit_transform(X)
        # print(a.shape)
        return a

    def ica(self, X):
        X = (X - np.mean(X, axis=0)) / np.std(X, axis=0)
        # print(X.shape)
        return self._ica.fit_transform(X)

    def record(self, path='./processor_data', recording_length=10):
        if not self.is_recording:
            self._save_path = os.path.realpath(path)
            self.recorded_data = []
            self.is_recording = True
            self.data.pipe(take_until_with_time(recording_length)).subscribe(
                observer=lambda values: self.recorded_data.append(values),
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
        self._is_open = True
        sleep(1.5)
        for subscription in self.subscriptions:
            try:
                subscription.dispose()
            except DisposedException:
                pass
        print('Processor Closed!')


if __name__ == '__main__':
    connector = Connector()
    processor = Processor()
    print('test')
    connector.data.subscribe(processor.add_data)  # using higher order function
    processor.data.subscribe(lambda value: print(value))  # using lambda function
    sleep(10)
    counter = 0
    while counter < 1000:
        counter += 1
    connector.close()
    processor.close()
