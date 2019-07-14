#!/usr/bin/env python3

import threading
import socket
import numpy as np
import os
from json import loads
from time import sleep, time
from math import floor
from rx.subject import Subject
from rx.operators import take_while, take_until_with_time


class Connector(object):
    def __init__(self, debug=False, verbose=False):  # type: (NeuroSky, bool, bool) -> None
        # Global            
        self._DEBUG = debug
        self._VERBOSE = verbose

        # disposal handler
        self.subscriptions = []

        # Observables and Subjects
        self.data = Subject()
        self.subscriptions.append(self.data)
        self.poor_signal_level = Subject()
        self.subscriptions.append(self.poor_signal_level)
        self.sampling_rate = Subject()
        self.subscriptions.append(self.sampling_rate)

        # Hidden Params
        self._sampling_rate_counter = 0
        self._is_open = True
        self._save_path = ''

        # Editable Params
        self.is_recording = False
        self.recorded_data = []

        # Connection initializer
        self.client_socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)

        # Data Generator initializer
        self._init_thread(target=self._generate_data)

    @staticmethod
    def _init_thread(target, args=()):
        threading.Thread(target=target, args=args).start()

    def _generate_sampling_rate(self):  # type: (NeuroSky) -> None
        while self._is_open:
            self._sampling_rate_counter = 0
            sleep(1)
            self.sampling_rate.on_next(self._sampling_rate_counter)

    def _generate_data(self):  # type: (NeuroSky) -> None
        if self._DEBUG:
            self._init_thread(target=self._generate_sampling_rate)
            while self._is_open:
                gaussian_num = floor(np.random.normal(0, 150, 1)[0])
                if -150 < gaussian_num < 150:
                    self.data.on_next(gaussian_num)
                    self.poor_signal_level.on_next(np.random.randint(0, 100))
                    self._sampling_rate_counter += 1

        else:
            try:
                self.client_socket.connect(('127.0.0.1', 13854))
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
                            except:
                                if len(json_data) > 3:
                                    self.poor_signal_level.on_next(json_data['eSense']['poorSignalLevel'])
                                else:
                                    self.poor_signal_level.on_next(json_data['poorSignalLevel'])
                        except:
                            continue
                    if self.poor_signal_level is 200 and self._VERBOSE:
                        print('Poor Connections!')
            except:
                print('An error occurred, are you connected?')
                self.close()

    def record(self, path='./connector_data', recording_length=10):
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

    def _save(self):  # type: (Connector) -> None
        np.save(self._save_path, self.recorded_data)
        self.is_recording = False
        print('Recording Complete')

    def close(self):  # type: (Connector) -> None
        self._is_open = False
        self.is_recording = False
        print('Closing Connection...')
        sleep(2)  # Wait for the threads to finalise. ToDo: Consider adding frame rate sleep.
        # Dispose of subjects, as subscription type.
        for subscription in self.subscriptions:
            subscription.dispose()
        try:
            self.client_socket.close()
        finally:
            print('Connection Closed!')


if __name__ == '__main__':
    connector = Connector(debug=True, verbose=False)
    connector.data.subscribe(on_next=print, on_error=print)
    connector.sampling_rate.subscribe(on_next=lambda value: print('Sampling Rate: {0}'.format(value)))
    connector.poor_signal_level.subscribe(on_next=lambda value: print('Poor Signal Level: {0}'.format(value)))
    connector.record()
    while connector.is_recording:
        pass
    connector.close()
