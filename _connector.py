#!/usr/bin/env python3

import threading
import socket
from json import loads
from numpy import random
from time import sleep
from math import floor
from rx.subjects import Subject


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
                gaussian_num = floor(random.normal(0, 150, 1)[0])
                if -150 < gaussian_num < 150:
                    self.data.on_next(gaussian_num)
                    self.poor_signal_level.on_next(random.randint(0, 100))
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
                                self.data.on_next(json_data['rawEeg'])
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

    def close(self):  # type: (Connector) -> None
        self._is_open = False
        try:
            self.client_socket.close()
        finally:
            print('Connection Closed!')

        # Dispose of subjects, as subscription type.
        for subscription in self.subscriptions:
            subscription.dispose()


if __name__ == '__main__':
    connector = Connector(debug=True, verbose=False)
    connector.data.subscribe(lambda value: print(value))
    connector.sampling_rate.subscribe(lambda value: print('Sampling Rate: {0}'.format(value)))
    counter = 0
    while counter < 1000:
        counter += 1
    connector.close()
