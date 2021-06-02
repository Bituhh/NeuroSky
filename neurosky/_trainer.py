#!/usr/bin/env python3
import json
import os
from functools import wraps
from typing import Any, Type

from rx.internal import DisposedException

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
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.decomposition import PCA
from rx.subject import Subject
import numpy as np


class Trainer(object):  # type: Type[Trainer]
    def __init__(self, classifier_name='MLP'):
        super(Trainer, self).__init__()
        # Classifier initialiser
        self.classifier_name = classifier_name
        classifiers = {
            'RandomForest': RandomForestClassifier(n_estimators=10),
            'MLP': MLPClassifier(
                solver='adam',
                alpha=1,
                # hidden_layer_sizes=(100, 100, 100, 100, 100),
                verbose=True,
                shuffle=True,
                warm_start=True,
                learning_rate='adaptive',
            ),
            'SVC': SVC(gamma='auto'),
            'KNN': KNeighborsClassifier(n_neighbors=3),
            'AdaBoost': AdaBoostClassifier(
                n_estimators=100,
                learning_rate=0.05,
                random_state=0,
            )
        }
        self.cls = classifiers[classifier_name]
        self.pca = PCA(n_components=2)
        self._is_open = True

        # Observables and Subjects
        self.prediction = Subject()
        self.status = Subject()
        self.identifiers = Subject()

        # disposal handler
        self.subscriptions = []
        self.subscriptions.append(self.prediction)
        self.subscriptions.append(self.status)
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
        self.training_summary = []

        # Prediction initialiser
        self._identifiers = []

        # self._init_thread(target=self._initialise_classifier, args=(classifier_name,))

    @staticmethod
    def _init_thread(target, args=()):
        Thread(target=target, args=args).start()

    def add_data(self, data):  # type: (Trainer, Any) -> None
        self.current_data = data
        if self._is_recording_data:
            self.recorded_data.append(data)
            self.samples.append(data)
            self.targets.append(self.current_training_target)
            self.accumulative_samples.append(data)
            self.accumulative_targets.append(self.current_training_target)
        else:
            self.predict()

    def _initialise_classifier(self, classifier_name):
        self.status.on_next('Initialising Trainer...')
        for i in range(int(len(os.listdir('./data')) / 2)):
            arm_down_data = np.load('./data/arm_down_processor_' + str(i + 1) + '.npy')
            for data in arm_down_data:
                # print(data)
                self.accumulative_samples.append(data[1])
                self.accumulative_targets.append(1)
                self.samples.append(data[1])
                self.targets.append(1)
            arm_up_data = np.load('./data/arm_up_processor_' + str(i + 1) + '.npy')
            for data in arm_up_data:
                self.accumulative_samples.append(data[1])
                self.accumulative_targets.append(0)
                self.samples.append(data[1])
                self.targets.append(0)
        # print(np.array(self.samples).shape)
        if classifier_name == 'RandomForest':
            self._init_thread(self._random_forest.__wrapped__, args=(self,))
        elif classifier_name == 'MLP':
            self._init_thread(self._mlp.__wrapped__, args=(self,))
        elif classifier_name == 'SVC':
            self._init_thread(self._svc.__wrapped__, args=(self,))
        elif classifier_name == 'KNN':
            self._init_thread(self._knn.__wrapped__, args=(self,))
        elif classifier_name == 'AdaBoost':
            self._init_thread(self._adaboost.__wrapped__, args=(self,))

    def train(self, identifier_name):  # type: (Trainer, Any) -> None
        if self._is_open:
            for identifier in self._identifiers:
                if identifier['name'] is identifier_name:
                    self.current_training_target = identifier['target']
                    identifier['training_count'] += 1
                    self._update_identifiers()
                    break

            if self.classifier_name == 'RandomForest':
                print('RandomForest')
                self._init_thread(target=self._random_forest)
            elif self.classifier_name == 'MLP':
                print('MLP')
                self._init_thread(target=self._mlp)
            elif self.classifier_name == 'SVC':
                print('SVC')
                self._init_thread(target=self._svc)
            elif self.classifier_name == 'KNN':
                print('KNN')
                self._init_thread(target=self._knn)

    def _training(func):
        @wraps(func)
        def wrapper(self):
            if not self._is_training:
                # Set training flag and status
                identifier_name = 'arm_up'
                for identifier in self._identifiers:
                    if identifier['target'] is self.current_training_target:
                        identifier_name = identifier['name']
                        break
                self.status.on_next('Training for {0}...'.format(identifier_name))
                self._is_training = True
                sleep(self.training_wait_time)
                self.status.on_next('Recording data...')
                self.recorded_data = []
                self.samples = []
                self.targets = []
                self._is_recording_data = True
                sleep(self.recording_time)
                self._is_recording_data = False
                np.save('./data/' + self.get_next_processor_label(identifier_name), self.recorded_data)
                self.status.on_next('Scoring data...')
                score = self.cls.score(self.samples, self.targets)
                print('Current Score is {0}'.format(score))
                self.status.on_next('Fitting data...')
                start_time = time()
                func(self)
                training_time = time() - start_time
                print(training_time)
                print('Current Score is {0}'.format(self.cls.score(self.samples, self.targets)))
                self.training_summary.append({
                    'score': score,
                    'identifier_name': identifier_name,
                    'time_elapse': training_time,
                    'total_sample_size': len(self.accumulative_samples),
                    'total_target_size': len(self.accumulative_targets),
                    'classifier_name': self.classifier_name
                })
                self._is_training = False
                self.status.on_next('Training Complete')

        return wrapper

    @_training
    def _random_forest(self):
        self.cls.n_estimators += 1
        self.cls.fit(self.accumulative_samples, self.accumulative_targets)
        self.is_trained = True

    @_training
    def _mlp(self):
        self.cls.fit(self.accumulative_samples, self.accumulative_targets)
        print(self.cls.loss_)
        self.is_trained = True

    @_training
    def _svc(self):
        self.cls.fit(self.accumulative_samples, self.accumulative_targets)
        self.is_trained = True

    @_training
    def _knn(self):
        self.cls.fit(self.accumulative_samples, self.accumulative_targets)
        self.is_trained = True

    @_training
    def _adaboost(self):
        self.cls.fit(self.accumulative_samples, self.accumulative_targets)
        self.is_trained = True

    def predict(self):  # type: (Trainer) -> None
        def _predict():
            if self.is_trained and not self._is_training:
                self.status.on_next('Predicting...')
                # try:
                # if self.classifier_name == 'SVC':
                #     self.pca.fit_transform(self.)
                print(np.array(self.current_data).shape)
                train_data = np.array(self.current_data).reshape(1, -1)
                prediction = self.cls.predict(train_data)[0]
                for identifier in self._identifiers:
                    if prediction == identifier['target']:
                        self.prediction.on_next(identifier['name'])
                # except:
                #     print('An error occurred on prediction, prediction not performed!')

        if self._is_open:
            self._init_thread(target=_predict)

    # State Management
    def add_identifier(self, identifier_name):  # type: (Trainer, str) -> str
        identifier = {
            'name': identifier_name,
            'target': len(self._identifiers),
            'connector_index': 0,
            'processor_index': int(len(os.listdir('./data')) / 2),
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
        self._is_open = False
        sleep(0.5)
        if len(self.training_summary) > 0:
            with open('./neurosky/score.json', 'r') as file:
                saved_data = json.loads(file.read())
                saved_data.append(self.training_summary)
                data_to_save = json.dumps(saved_data)
            with open('./neurosky/score.json', 'w+') as file:
                file.write(data_to_save)
        for subscription in self.subscriptions:
            try:
                subscription.dispose()
            except DisposedException:
                pass


class _TestTrainer:
    def __init__(self):
        self.counter = 0
        self.signal_status = 'Poor Signal'

        self.connector = Connector()
        self.processor = Processor(live=True)
        self.trainer = Trainer(classifier_name='RandomForest')  # 'MLP' || 'RandomForest' || 'SVC' || 'KNN' || 'AdaBoost'

        self.connector.data.subscribe(self.processor.add_data)
        self.connector.sampling_rate.subscribe(self.processor.set_sampling_rate)
        self.connector.poor_signal_level.subscribe(self.check_poor_level)

        self.processor.data.subscribe(self.trainer.add_data)
        self.trainer.status.subscribe(print)
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
        self.processor.record('./data/' + self.trainer.get_next_processor_label(identifier_name))
        while self.processor.is_recording:
            print(time() - start_time)
        self.counter += 1

    def close_all(self):
        self.trainer.close()
        self.processor.close()
        self.connector.close()
        self.key_handler.stop()

    def check_poor_level(self, level):
        if level > 0:
            if self.signal_status is not 'Poor Signal':
                print('Poor Signal')
                self.signal_status = 'Poor Signal'
        else:
            if self.signal_status is not 'Good Signal':
                print('Good Signal')
                self.signal_status = 'Good Signal'


if __name__ == '__main__':
    test = _TestTrainer()
