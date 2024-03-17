#!/usr/bin/env python3

import threading
import os
from typing import Tuple, Callable

import numpy as np
from time import sleep

from sklearn.decomposition import PCA
from sklearn.decomposition import FastICA

try:
    from neurosky._connector import Connector
except ModuleNotFoundError:
    from connector import Connector

from rx3.internal import DisposedException
from rx3.subject import Subject
from rx3.operators import take_until_with_time


class Processor(object):
    def __init__(self, batch_mode: bool = False, live: bool = False):
        # Editable params
        self._is_live_recording: bool = live
        self.data_resolution: int = 250
        self.blink_threshold: int = 50000000
        self.recorded_data: list[int] = []
        self.is_recording: bool = False
        self._is_open: bool = True
        self._sample_frequency: int = 512
        self.batch_mode: bool = batch_mode
        self.processed_data: list[int] = []

        # Disposal handler
        self.subscriptions: list[Subject] = []

        # Observers and Subjects
        self.data: Subject = Subject()
        self.subscriptions.append(self.data)

        # Hidden params
        self._raw_data_batch: list[int] = []
        self._save_path: str = ''

        split: int = 50

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
    def _init_thread(target: Callable, args: Tuple = ()) -> None:
        threading.Thread(target=target, args=args).start()

    def add_data(self, raw_data: int):
        if not self.batch_mode:
            self._raw_data_batch.append(raw_data)
            if len(self._raw_data_batch) >= self.data_resolution and self._is_open:
                self._init_thread(target=self._fft)

    def fft(self, data_batch):
        if self.batch_mode:
            for data in data_batch:
                self._raw_data_batch.append(data)
            self._fft()

    def set_sampling_rate(self, fs: int) -> None:
        self._sample_frequency = fs

    def _fft(self) -> None:
        temp_data_batch = self._raw_data_batch.copy()
        self._raw_data_batch: list[int] = []
        batch_size: int = len(temp_data_batch)
        print(batch_size)
        if batch_size != 0 and (
                self.blink_threshold > np.amax(temp_data_batch) or -self.blink_threshold < np.amin(temp_data_batch)):
            x_fft = np.fft.rfftfreq(batch_size, 2 * (1 / self._sample_frequency))
            if self._is_live_recording:
                slice_size: int = 48
            else:
                slice_size: int = round(len(list(filter(lambda x: x < 50, x_fft))), -1)
            # slice_size = 100
            x_fft = x_fft[:slice_size]
            # print(max(x_fft))
            y_fft = np.absolute(np.real(np.fft.rfft(temp_data_batch)))[:slice_size]
            # print(len(y_fft))
            self.processed_data = np.array([x_fft, y_fft])[1]
            self.data.on_next(self.processed_data)

    def pca(self, x: int):
        x = (x - np.mean(x, axis=0)) / np.std(x, axis=0)
        # print(X.shape)
        a = self._pca.fit_transform(x)
        # print(a.shape)
        return a

    def ica(self, x: int):
        x = (x - np.mean(x, axis=0)) / np.std(x, axis=0)
        # print(X.shape)
        return self._ica.fit_transform(x)

    def record(self, path: str = './processor_data', recording_length: int = 10) -> None:
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

    def _save(self) -> None:
        np.save(self._save_path, self.recorded_data)
        self.is_recording = False
        print('Recording Complete')

    def close(self) -> None:
        self._is_open = True
        sleep(1.5)
        for subscription in self.subscriptions:
            try:
                subscription.dispose()
            except DisposedException:
                pass
        print('Processor Closed!')

    def __enter__(self) -> ['Processor']:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


if __name__ == '__main__':
    with Connector() as connector:
        with Processor() as processor:
            connector.data.subscribe(processor.add_data)  # using higher order function
            processor.data.subscribe(lambda value: print(value))  # using lambda function
            sleep(10)
