#!/usr/bin/env python3
import os
from functools import wraps
from typing import Any, Type

try:
    from neurosky.utils import KeyHandler
    from neurosky._connector import Connector
    from neurosky._processor import Processor
except ModuleNotFoundError:
    # noinspection PyUnresolvedReferences
    from utils import KeyHandler
    # noinspection PyUnresolvedReferences
    from _connector import Connector
    # noinspection PyUnresolvedReferences
    from _processor import Processor

from threading import Thread
from time import sleep, time
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from rx.subject import Subject
import numpy as np


class Trainer(object):  # type: Type[Trainer]
    def __init__(self, classifier_name='MLP'):
        # Classifier initialiser
        super(Trainer, self).__init__()
        self.classifier = classifier_name
        classifiers = {
            'RandomForest': RandomForestClassifier(n_estimators=100, warm_start=True),
            'MLP': MLPClassifier(
                solver='lbfgs',
                hidden_layer_sizes=(1000, 1000, 1000, 1000, 1000),
                max_iter=1,
                warm_start=True
            )
        }
        self.cls = classifiers[classifier_name]

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
        self.recording_time = 10
        self._is_recording_data = False
        self.is_trained = False
        self._is_training = False
        self.current_training_target = None
        self.recorded_data = []
        self.samples = []
        self.targets = []
        self.accumulative_samples = []
        self.accumulative_targets = []

        # Prediction Params
        self.prediction_wait_time = 0.25
        self.current_data = []

        # Scoring Params
        self.scoring = []

        # Prediction initialiser
        self._identifiers = []
        self._initialise_classifier(classifier_name)



    @staticmethod
    def _init_thread(target, args=()):
        Thread(target=target, args=args).start()

    def add_data(self, data):  # type: (Trainer, Any) -> None
        self.current_data = data
        if self._is_recording_data:
            self.recorded_data.append(data)
            self.samples.append(data[0])
            self.targets.append(self.current_training_target)
            self.accumulative_samples.append(data[0])
            self.accumulative_targets.append(self.current_training_target)
        else:
            self.predict()

    def _initialise_classifier(self, classifier_name):
        for i in range(100):
            arm_down_data = np.load('./neurosky/data/arm_down_processor_' + str(i + 1) + '.npy')
            for data in arm_down_data:
                self.accumulative_samples.append(data[0])
                self.accumulative_targets.append(1)
                self.samples.append(data[0])
                self.targets.append(1)
            arm_up_data = np.load('./neurosky/data/arm_up_processor_' + str(i + 1) + '.npy')
            for data in arm_up_data:
                self.accumulative_samples.append(data[0])
                self.accumulative_targets.append(0)
                self.samples.append(data[0])
                self.targets.append(0)
        print(self.targets)
        if classifier_name == 'RandomForest':
            self._init_thread(self._random_forest.__wrapped__, args=(self,))
        elif classifier_name == 'MLP':
            self._init_thread(self._mlp.__wrapped__, args=(self,))

    def train(self, identifier_name):  # type: (Trainer, Any) -> None
        # Determining target
        for identifier in self._identifiers:
            if identifier['name'] is identifier_name:
                self.current_training_target = identifier['target']
                identifier['training_count'] += 1
                self._update_identifiers()
                break

        if self.classifier == 'RandomForest':
            print('RandomForest')
            self._init_thread(target=self._random_forest)
        elif self.classifier == 'MLP':
            print('MLP')
            self._init_thread(target=self._mlp)

    def _training(func):
        @wraps(func)
        def wrapper(self):
            # Set training flag and status
            self.training_status.on_next('Training for {0}...'.format(self.current_training_target))
            self._is_training = True
            sleep(self.training_wait_time)
            self.training_status.on_next('Recording data...')
            self.recorded_data = []
            self.samples = []
            self.targets = []
            self._is_recording_data = True
            sleep(self.recording_time)
            self._is_recording_data = False
            identifier_name = 'arm_up'
            for identifier in self._identifiers:
                if identifier['target'] is self.current_training_target:
                    identifier_name = identifier['name']
                    break
            np.save('./neurosky/data/' + self.get_next_processor_label(identifier_name), self.recorded_data)
            self.training_status.on_next('Scoring data...')
            self.scoring.append(self.cls.score(self.samples, self.targets))
            self.training_status.on_next('Fitting data...')
            start_time = time()
            func(self)
            print(time() - start_time)
            self._is_training = False
            self.training_status.on_next('Training Complete')
        return wrapper

    @_training
    def _random_forest(self):
        self.cls.n_estimators += 1
        print(np.array(self.accumulative_samples).shape)
        self.cls.fit(self.accumulative_samples, self.accumulative_targets)
        self.is_trained = True

    @_training
    def _mlp(self):
        print(np.array(self.samples).shape)
        self.cls.fit(self.samples, self.targets)
        self.is_trained = True

    def predict(self):  # type: (Trainer) -> None
        def _predict():
            if self.is_trained and not self._is_training:
                self.training_status.on_next('Predicting...')
                try:
                    prediction = self.cls.predict(self.current_data)[0]
                    for identifier in self._identifiers:
                        if prediction == identifier['target']:
                            self.prediction.on_next(identifier['name'])
                    # sleep(self.prediction_wait_time)
                except:
                    print('An error occurred on prediction, prediction not performed!')

        self._init_thread(target=_predict)

    # State Management
    def add_identifier(self, identifier_name):  # type: (Trainer, str) -> str
        identifier = {
            'name': identifier_name,
            'target': len(self._identifiers),
            'connector_index': 0,
            'processor_index': int(len(os.listdir('./neurosky/data'))/2),
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
                return identifier_name + '_processor_' + str(identifier['processor_index'])

    def close(self):  # type: (Trainer) -> None
        for subscription in self.subscriptions:
            subscription.dispose()


class _TestTrainer:
    def __init__(self):
        self.counter = 0

        self.connector = Connector(debug=False, verbose=False)
        self.processor = Processor()
        self.trainer = Trainer(classifier_name='RandomForest')  # 'MLP'

        self.connector.data.subscribe(self.processor.add_data)
        self.connector.sampling_rate.subscribe(self.processor.set_sampling_rate)
        self.connector.poor_signal_level.subscribe(print)

        self.processor.data.subscribe(self.trainer.add_data)
        # self.trainer.training_status.subscribe(print)
        self.trainer.prediction.subscribe(print)

        self.IDENTIFIER_ARM_UP = self.trainer.add_identifier('arm_up')
        self.IDENTIFIER_ARM_DOWN = self.trainer.add_identifier('arm_down')
        self.IDENTIFIER_IDLE = self.trainer.add_identifier('idle')

        self.key_handler = KeyHandler()
        self.key_handler.add_key_event(key='q', event=self.close_all)
        self.key_handler.add_key_event(key='1', event=self.trainer.train, identifier_name=self.IDENTIFIER_ARM_UP)
        self.key_handler.add_key_event(key='2', event=self.trainer.train, identifier_name=self.IDENTIFIER_ARM_DOWN)
        # self.key_handler.add_key_event(key='3', event=self.trainer.train, identifier_name=self.IDENTIFIER_IDLE)
        self.key_handler.add_key_event(key='p', event=self.trainer.predict)
        self.key_handler.start()

    def record(self, identifier_name):
        start_time = time()
        self.processor.record('./neurosky/data/' + self.trainer.get_next_processor_label(identifier_name))
        while self.processor.is_recording:
            print(time() - start_time)
        self.counter += 1

    def close_all(self):
        self.trainer.close()
        self.processor.close()
        self.connector.close()
        self.key_handler.stop()


if __name__ == '__main__':
    test = _TestTrainer()
