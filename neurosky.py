#!/usr/bin/env python3

import threading
import socket
import matplotlib.pyplot as plt
from scipy.fftpack import fft, ifft
from json import loads
from msvcrt import kbhit, getch
from numpy import random, linspace, array
from time import sleep
from math import floor


class NeuroSky(object):
    def __init__(self, debug=False, verbose=False):
        self.verbose = verbose
        self.raw_data = 0
        self.raw_data_batch = []
        self.fft_data = []
        self.poor_signal_level = 0
        self.counter = 0
        self.CLOSED = False
        self.AVAILABLE = False
        self.addr = '127.0.0.1'
        self.port = 13854
        self.sampling_rate = 0
        self.init_thread(target=self.keypress_handler,
                         msg='Initialising keypress handler...')
        if debug:
            self.init_thread(target=self.get_random_data,
                             msg='Initialising data retreaver...')
        else:
            self.init_thread(target=self.get_data,
                             msg='Initialising data retreaver...')

    def get_sampling_rate(self):
        while not self.CLOSED:
            self.counter = 0
            sleep(1)
            self.sampling_rate = self.counter
            if self.verbose:
                print(self.counter, "per sec")

    def get_random_data(self):
        self.init_thread(target=self.get_sampling_rate,
                         msg='Initialising timer...')
        while not self.CLOSED:
            gaussian_num = floor(random.normal(0, 150, 1)[0])
            if gaussian_num > -150 and gaussian_num < 150:
                self.raw_data = gaussian_num
                self.raw_data_batch.append(self.raw_data)
                self.poor_signal_level = random.randint(0, 100)
                self.counter += 1
                if len(self.raw_data_batch) >= 250:
                    self.init_thread(target=self.computer_fft,
                                     msg='Initialising FFT...')

    def get_data(self):
        self.client_socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        self.client_socket.connect((self.addr, self.port))
        self.client_socket.sendall(
            bytes('{"enableRawOutput":true,"format":"Json"}'.encode('ascii')))
        contains = False
        self.init_thread(target=self.get_sampling_rate,
                         msg='Initialising timer...')
        if self.verbose:
            print('Retreaving data...')
        while not self.CLOSED:
            raw_bytes = self.client_socket.recv(1000)
            data_set = (str(raw_bytes)[2:-3].split(r'\r'))
            for data in data_set:
                self.counter += 1
                try:
                    json_data = loads(data)
                    try:
                        self.raw_data = json_data['rawEeg']
                        self.raw_data_batch.append(self.raw_data)
                    except:
                        if len(json_data) > 3:
                            self.poor_signal_level = self.raw_data = json_data['eSense']['poorSignalLevel']
                        else:
                            self.poor_signal_level = self.raw_data = json_data['poorSignalLevel']
                except:
                    continue
                if len(self.raw_data_batch) >= 250:
                    self.init_thread(target=self.computer_fft,
                                     msg='Initialising FFT...')
            if self.poor_signal_level is 200 and self.verbose:
                print('Poor Connections!')
        self.client_socket.close()

    def computer_fft(self):
        tmp = self.raw_data_batch.copy()
        self.raw_data_batch = []
        self.fft_data = []
        batch_size = len(tmp)
        x_fft = linspace(0, 1 / (2 * (1 / 512)), batch_size / 2)
        y_fft = fft(tmp)
        self.fft_data.append(x_fft)
        self.fft_data.append(y_fft)

    # def plot(self):
    #     x = []
    #     y = []
    #     i = 0
    #     plt.autoscale(enable=True, axis='both', tight=None)
    #     while not self.CLOSED and plt.get_fignums():
    #         if i > 1:
    #             x.pop(0)
    #             y.pop(0)
    #         x.append(i)
    #         y.append(self.raw_data)
    #         plt.plot(x, y, 'g-')
    #         plt.pause(0.01)
    #         i += 1
    #     plt.close()

    def keypress_handler(self):
        print('Press ESC to quit at any time!')
        while not self.CLOSED:
            # if ESC key is press stop running and close socket
            if kbhit() and ord(getch()) is 27:
                self.CLOSED = True

    def init_thread(self, target, msg):
        if self.verbose:
            print(msg)
        process = threading.Thread(target=target)
        process.start()


if __name__ == '__main__':
    neuro = NeuroSky(debug=True, verbose=True)
    # neuro.get_sampling_rate()
