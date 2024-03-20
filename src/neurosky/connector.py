#!/usr/bin/env python3

import threading
import socket
from typing import Callable, Tuple

import numpy as np
import os
from json import loads
from time import sleep
from math import floor
from rx3.internal import DisposedException
from rx3.subject import Subject
from rx3.operators import take_until_with_time


class Connector(object):
    def __init__(self, debug: bool = False, verbose: bool = False, hostname: str = '127.0.0.1', port: int = 13854) -> None:
        # Global
        self._DEBUG: bool = debug
        self._VERBOSE: bool = verbose
        self._HOSTNAME: str = hostname
        self._PORT: int = port

        # disposal handler
        self.subscriptions: list[Subject] = []

        # Observables and Subjects
        self.data: Subject = Subject()
        self.subscriptions.append(self.data)

        self.poor_signal_level: Subject = Subject()
        self.subscriptions.append(self.poor_signal_level)

        self.sampling_rate = Subject()
        self.subscriptions.append(self.sampling_rate)

        # Hidden Params
        self._sampling_rate_counter: int = 0
        self._is_open: bool = True
        self._save_path: str = ''

        # Editable Params
        self.is_recording: bool = False
        self.recorded_data: list[int] = []

        # Connection initializer
        self.client_socket: socket.socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)

    def start(self):
        self._init_thread(target=self._generate_data)

    @staticmethod
    def _init_thread(target: Callable, args: Tuple = ()) -> None:
        threading.Thread(target=target, args=args).start()

    def _generate_sampling_rate(self) -> None:
        while self._is_open:
            self._sampling_rate_counter = 0
            sleep(1)
            self.sampling_rate.on_next(self._sampling_rate_counter)

    def _generate_data(self) -> None:
        if self._DEBUG:
            self._init_thread(target=self._generate_sampling_rate)
            while self._is_open:
                gaussian_num = floor(np.random.normal(0, 150, 1)[0])
                if -150 < gaussian_num < 150:
                    self.data.on_next(gaussian_num)
                    self.poor_signal_level.on_next(np.random.randint(0, 100))
                    self._sampling_rate_counter += 1
                    sleep(0.00001)

        else:
            try:
                self.client_socket.connect((self._HOSTNAME, self._PORT))
                self.client_socket.sendall(bytes('{"enableRawOutput":true,"format":"Json"}'.encode('ascii')))
                self._init_thread(target=self._generate_sampling_rate)
                if self._VERBOSE:
                    print('Retrieving data...')
                while self._is_open:
                    raw_bytes = self.client_socket.recv(1000)
                    data_set = (str(raw_bytes)[2:-3].split(r'\r'))
                    for data in data_set:
                        self._sampling_rate_counter += 1
                        try:
                            json_data = loads(data)
                            try:
                                temp_data = json_data['rawEeg']
                                self.data.on_next(temp_data)
                            except:  # Key Access Error - TODO: add specific exception
                                if len(json_data) > 3:
                                    self.poor_signal_level.on_next(json_data['eSense']['poorSignalLevel'])
                                else:
                                    self.poor_signal_level.on_next(json_data['poorSignalLevel'])
                        except:  # JSONDecodeError - TODO: add specific exception
                            continue
                    if self.poor_signal_level == 200 and self._VERBOSE:
                        print('Poor Connections!')
            except (ConnectionError, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError):
                print('An error connection occurred, are you connected?')
                self.close()
                raise ConnectionError('An error connection occurred, are you connected?')

    def record(self, path='./connector_data', recording_length=10) -> None:
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

    def _save(self) -> None:
        np.save(self._save_path, self.recorded_data)
        self.is_recording = False
        print('Recording Complete')

    def await_recording(self) -> None:
        while self.is_recording:
            pass

    def close(self) -> None:
        self._is_open = False
        self.is_recording = False
        sleep(1.5)  # Wait for the threads to finalise. ToDo: Consider adding frame rate sleep.
        # Dispose of subjects, as subscription type.

        for subscription in self.subscriptions:
            try:
                subscription.dispose()
            except DisposedException:
                pass
        try:
            self.client_socket.close()
        finally:
            print('Connection Closed!')

    def __enter__(self):
        # Data Generator initializer
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    with Connector() as connector:
        connector.data.subscribe(on_next=print)
        connector.sampling_rate.subscribe(on_next=lambda value: print('Sampling Rate: {0}'.format(value)))
        connector.poor_signal_level.subscribe(on_next=lambda value: print('Poor Signal Level: {0}'.format(value)))
        connector.record()
        connector.await_recording()
