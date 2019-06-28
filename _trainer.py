#!/usr/bin/env python3

import threading
import matplotlib.pyplot as plt

from _connector import Connector
from _processor import Processor

from time import sleep, time
from numpy import array_equal, array
from scipy.signal import savgol_filter, butter, lfilter
from sklearn.decomposition import FastICA
from sklearn.ensemble import RandomForestClassifier


class Trainer(object):
    def __init__(self):
        # Classifier Initializer
        self.cls = RandomForestClassifier(n_estimators=100)

        # Training Parameters
        self.is_trained = False

        self.prediction = 0
        self.prediction_status = 'Initialising...'
        self.training_counter = 0
        self.sample = []
        self.target = []
        self.confidence_level = []
        self._init_thread(target=self.predict)

    @staticmethod
    def _init_thread(target, args=()):
        threading.Thread(target=target, args=args).start()

    def train(self, target):
        self._init_thread(target=self._train_thread, args=(target,))

    def _train_thread(self, target):
        # self.cls.n_estimators += 1
        # try:
        self.prediction_status = 'Waiting 3 sec...'
        sleep(3)
        self.prediction_status = 'Recording Data...'
        recorded_data = []
        recorded_target = []
        start_time = time()
        previous = array([])
        while (time() - start_time) < 3:
            current = self.fft_data[1]
            if not array_equal(current, previous):
                recorded_data.append(current)
                recorded_target.append(int(target))
                previous = current
        self.prediction_status = 'Storing Data...'
        for i in range(len(recorded_data)):
            self.sample.append(recorded_data[i])
            self.target.append(recorded_target[i])
        has_confidence_level = False
        if self.is_trained:
            self.prediction_status = 'Scoring Data...'
            self.confidence_level.append(
                [self.cls.score(recorded_data, recorded_target), self.training_counter, int(target)])
            print(self.confidence_level[-1])
            has_confidence_level = True
        self.is_trained = False
        self.prediction_status = 'Training...'
        self.cls.n_estimators += 1
        training_start_time = time()
        self.cls.fit(self.sample, self.target)
        if has_confidence_level:
            self.confidence_level[-1].append(time() - training_start_time)
            print(self.confidence_level[-1][2])
        print('done fitting')
        self.is_trained = True
        self.prediction_status = 'Ready...'
        self.training_counter += 1
        # except:
        #     print('Error on training!')
        #     pass
    #
    # def predict(self):
    #     while not self.is_closed:
    #         try:
    #             if self.is_trained and (
    #                     self.prediction_status not in ['Waiting 3 sec...', 'Recording Data...', 'Storing Data...',
    #                                                    'Scoring Data...']):
    #                 self.prediction_status = 'Prediction...'
    #                 # print(len(self.fft_data[1]), '< y .... x >', len(self.fft_data[0]))
    #                 if self.cls.predict([self.fft_data[1]])[0] == 0:
    #                     self.prediction = 'Arm Up'
    #                 else:
    #                     self.prediction = 'Arm Down'
    #                 sleep(0.25)
    #         except:
    #             pass
    #             print('Error on predicting!')


if __name__ == '__main__':
    connector = Connector(debug=True, verbose=False)
    processor = Processor()
    processor.fft_data.subscribe(lambda value: print(value))

    while connector.is_open:
        processor.append_data(connector.data)
