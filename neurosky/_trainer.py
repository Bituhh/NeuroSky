#!/usr/bin/env python3
from utils import KeyHandler

from _connector import Connector
from _processor import Processor
from threading import Thread
from time import sleep, time
from sklearn.ensemble import RandomForestClassifier
from rx.subject import Subject
import numpy as np


class Trainer(object):
    def __init__(self):
        # Classifier Initializer
        super(Trainer, self).__init__()
        self.cls = RandomForestClassifier(n_estimators=100)

        # disposal handler
        self.subscriptions = []

        # Observables and Subjects
        self.prediction = Subject()
        self.subscriptions.append(self.prediction)

        # Training Params
        self.training_wait_time = 3
        self.recording_time = 3
        self._is_recording_data = False
        self.is_trained = False
        self._is_training = False
        self.current_training_target = None
        self.sample = []
        self.target = []
        # self.training_counter = 0

        # Prediction Params
        self.prediction_wait_time = 0.25
        self.current_data = []

        # Prediction Initializer
        # self.confidence_level = []
        self._prediction_identifiers = []
        # self._init_thread(target=self.predict)

        '''
        Handling data steps:
        wait a time interval
        record data for a set time interval
        score data if previously trained
        train on data set.
        '''

    @staticmethod
    def _init_thread(target, args=()):
        Thread(target=target, args=args).start()

    def add_data(self, data):
        self.current_data = data
        if self._is_recording_data:
            for data in self.current_data:
                self.sample.append(data)
                self.target.append(self.current_training_target)

    def train(self, target):
        self._is_training = True
        for identifiers in self._prediction_identifiers:
            if identifiers['name'] is target:
                self.current_training_target = identifiers['target']
                break
        sleep(self.training_wait_time)
        self._is_recording_data = True
        sleep(self.recording_time)
        self._is_recording_data = False
        # score previous training
        # if self.is_previously_trained:
        #     self.confidence_level.append(
        #         [self.cls.score(recorded_data, recorded_target), self.training_counter, int(target)])
        #     print(self.confidence_level[-1])
        #     has_confidence_level = True
        self.cls.n_estimators += 1
        training_start_time = time()
        self.cls.fit(self.sample, self.target)
        print(time() - training_start_time)
        self._is_training = False
        # if has_confidence_level:
        #     self.confidence_level[-1].append(time() - training_start_time)
        #     print(self.confidence_level[-1][2])
        # print('done fitting')
        self.is_trained = True
        # self.prediction_status = 'Ready...'
        # self.training_counter += 1

    def add_prediction_identifier(self, name):
        self._prediction_identifiers.append({'name': name, 'target': len(self._prediction_identifiers) - 1})

    def predict(self):
        if self.is_trained and not self._is_training:
            try:
                prediction = self.cls.predict(self.current_data)[0]
                for identifier in self._prediction_identifiers:
                    if prediction is identifier['target']:
                        print(identifier['name'])
                        self.prediction = identifier['name']
                sleep(self.prediction_wait_time)
            except:
                print('An error occurred on prediction, prediction not performed!')

    def close(self):
        for subscription in self.subscriptions:
            subscription.dispose()


class _TestTrainer:
    def __init__(self):
        self.connector = Connector(debug=True, verbose=False)
        self.processor = Processor()
        self.trainer = Trainer()

        self.connector.data.subscribe(self.processor.add_data)
        self.processor.data.subscribe(self.trainer.add_data)

        self.trainer.add_prediction_identifier('Up')
        self.trainer.add_prediction_identifier('Down')

        self.key_handler = KeyHandler()
        self.key_handler.add_key_event(key='q', event=self.close_all)
        self.key_handler.add_key_event(key='1', event=self.trainer.train, target='Up')
        self.key_handler.add_key_event(key='2', event=self.trainer.train, target='Down')
        self.key_handler.add_key_event(key='p', event=self.trainer.predict)
        self.key_handler.start()

    def close_all(self):
        self.connector.close()
        self.processor.close()
        self.trainer.close()
        self.key_handler.stop()


if __name__ == '__main__':
    test = _TestTrainer()
