#!/usr/bin/env python3
from neurosky.utils import KeyHandler

from neurosky._connector import Connector
from neurosky._processor import Processor
from threading import Thread
from time import sleep, time
from sklearn.ensemble import RandomForestClassifier
from rx.subject import Subject
import numpy as np


class Trainer(object):  # type: Type[Trainer]
    def __init__(self):
        # Classifier Initializer
        super(Trainer, self).__init__()
        self.cls = RandomForestClassifier(n_estimators=100)

        # disposal handler
        self.subscriptions = []

        # Observables and Subjects
        self.prediction = Subject()
        self.subscriptions.append(self.prediction)
        self.training_status = Subject()
        self.subscriptions.append(self.training_status)
        self.identifiers = Subject()
        self.subscriptions.append(self.identifiers)

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
        self._identifiers = []
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

    def add_data(self, data):  # type: (Trainer, Any) -> None
        self.current_data = data
        if self._is_recording_data:
            for data in self.current_data:
                self.sample.append(data)
                self.target.append(self.current_training_target)
        else:
            self.predict()

    def train(self, target):  # type: (Trainer, Any) -> None
        def _train():
            self._is_training = True
            self.training_status.on_next('Training for {0}...'.format(target))
            for identifier in self._identifiers:
                if identifier['name'] is target:
                    self.current_training_target = identifier['target']
                    identifier['training_count'] += 1
                    self._update_identifiers()
                    break
            sleep(self.training_wait_time)
            self._is_recording_data = True
            self.training_status.on_next('Recording data...')
            sleep(self.recording_time)
            self._is_recording_data = False
            # score previous training
            # if self.is_previously_trained:
            #     self.confidence_level.append(
            #         [self.cls.score(recorded_data, recorded_target), self.training_counter, int(target)])
            #     print(self.confidence_level[-1])
            #     has_confidence_level = True
            self.cls.n_estimators += 1
            # training_start_time = time()
            self.training_status.on_next('Fitting data...')
            print(np.array(self.target).shape)
            self.cls.fit(self.sample, self.target)
            # print(time() - training_start_time)
            self._is_training = False
            # if has_confidence_level:
            #     self.confidence_level[-1].append(time() - training_start_time)
            #     print(self.confidence_level[-1][2])
            # print('done fitting')
            self.is_trained = True
            self.training_status.on_next('Training Complete')
            # self.prediction_status = 'Ready...'
            # self.training_counter += 1

        self._init_thread(target=_train)

    def predict(self):  # type: (Trainer) -> None
        def _predict():
            if self.is_trained and not self._is_training:
                self.training_status.on_next('Predicting...')
                try:
                    prediction = self.cls.predict(self.current_data)[0]
                    for identifier in self._identifiers:
                        if prediction == identifier['target']:
                            # print(identifier['name'])
                            self.prediction.on_next(identifier['name'])
                    sleep(self.prediction_wait_time)
                except:
                    print('An error occurred on prediction, prediction not performed!')

        self._init_thread(target=_predict)

    # State Management
    def add_identifier(self, identifier_name):  # type: (Trainer, str) -> str
        identifier = {
            'name': identifier_name,
            'target': len(self._identifiers),
            'connector_index': 0,
            'processor_index': 0,
            'training_count': 0
        }
        self._identifiers.append(identifier)
        self._update_identifiers()
        return identifier_name

    def _update_identifiers(self):  # type: (Trainer) -> None
        self.identifiers.on_next(self._identifiers)

    def get_next_connector_label(self, identifier_name):  # type: (Trainer, Any) -> Any
        for identifier in self._identifiers:
            if identifier['name'] is identifier_name:
                identifier['connector_index'] += 1
                self._update_identifiers()
                return identifier_name + '_connector_' + identifier['connector_index']

    def get_next_processor_label(self, identifier_name):  # type: (Trainer, Any) -> Any
        for identifier in self._identifiers:
            if identifier['name'] is identifier_name:
                identifier['processor_index'] += 1
                self._update_identifiers()
                return identifier_name + '_processor_' + identifier['processor_index']

    def close(self):  # type: (Trainer) -> None
        for subscription in self.subscriptions:
            subscription.dispose()


class _TestTrainer:
    def __init__(self):
        self.connector = Connector(debug=False, verbose=False)
        self.processor = Processor()
        self.trainer = Trainer()

        self.connector.data.subscribe(self.processor.add_data)
        self.processor.data.subscribe(self.trainer.add_data)

        self.trainer.add_identifier('Up')
        self.trainer.add_identifier('Down')

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
