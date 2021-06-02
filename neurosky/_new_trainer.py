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
from rx.subject import Subject
import numpy as np


class Trainer(object):  # type: Type[Trainer]
    def __init__(self, classifier_name='MLP'):
        super(Trainer, self).__init__()
        # Classifier initialiser
        self.classifier_name = classifier_name
        classifiers = {
            'RandomForest': RandomForestClassifier(
                n_estimators=100,  # 100, 80, 50, 40, 30
                max_features=None,
            ),
            'MLP': MLPClassifier(
                solver='adam',
                hidden_layer_sizes=(100, 100, 100, 100, 100),
                learning_rate='constant',
                max_iter=500,
            ),
            'SVC': SVC(gamma='scale'),
            'KNN': KNeighborsClassifier(
                n_neighbors=3
            ),
            'AdaBoost': AdaBoostClassifier(
                n_estimators=100,
                learning_rate=0.005,
            )
        }
        self.cls = classifiers[classifier_name]
        self._is_open = True

        # Observables and Subjects
        self.prediction = Subject()

        # disposal handler
        self.subscriptions = []
        self.subscriptions.append(self.prediction)

        # Training Params
        self.training_wait_time = 3
        self.recording_time = 10
        self._is_recording_data = False
        self.is_trained = False
        self._is_training = False
        self.current_identifier = None
        self.samples = []
        self.targets = []
        self.accumulative_samples = []
        self.accumulative_targets = []

        # Prediction Params
        self.prediction_wait_time = 0.25

        # Scoring Params
        self.training_summary = []

        # self._init_thread(target=self._initialise_classifier, args=(classifier_name,))

    @staticmethod
    def _init_thread(target, args=()):
        Thread(target=target, args=args).start()

    def add_data(self, X, y):
        for i in range(len(X)):
            self.samples.append(X[i])
            self.targets.append(y[i])
            self.accumulative_samples.append(X[i])
            self.accumulative_targets.append(y[i])

    def clear_data(self):  # type: (Trainer, Any) -> None
        self.samples = []
        self.targets = []
        self.accumulative_samples = []
        self.accumulative_targets = []

    def _train(self):  # type: (Trainer) -> None
        # print(self.classifier_name)
        if self.classifier_name == 'RandomForest':
            self._init_thread(self._random_forest.__wrapped__, args=(self,))
        elif self.classifier_name == 'MLP':
            self._init_thread(self._mlp.__wrapped__, args=(self,))
        elif self.classifier_name == 'SVC':
            self._init_thread(self._svc.__wrapped__, args=(self,))
        elif self.classifier_name == 'KNN':
            self._init_thread(self._knn.__wrapped__, args=(self,))
        elif self.classifier_name == 'AdaBoost':
            self._init_thread(self._adaboost.__wrapped__, args=(self,))
        sleep(5)
        self.samples = []
        self.targets = []

    def train(self, identifier):  # type: (Trainer, Any) -> None
        if self._is_open:
            self.current_identifier = identifier
            print(self.classifier_name)
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
                self._is_training = True
                score_before = self.cls.score(self.samples, self.targets)
                print('Current Score is {0}'.format(score_before))
                start_time = time()
                func(self)
                training_time = time() - start_time
                print('Training Time is {0}'.format(training_time))
                score_after = self.cls.score(self.samples, self.targets)
                print('New Score after training is {0}'.format(score_after))
                self.training_summary.append({
                    'identifier_name': self.current_identifier['name'],
                    'classifier_name': self.classifier_name,
                    'training_time': training_time,
                    'score_before_training': score_before,
                    'score_after_training': score_after,
                    'samples_size_scored_against': len(self.samples),
                    'total_processed_samples_size': len(self.accumulative_samples),
                })
                self.samples = []
                self.targets = []
                self._is_training = False

        return wrapper

    @_training
    def _random_forest(self):
        self.cls.n_estimators += 1
        self.cls.fit(self.accumulative_samples, self.accumulative_targets)
        self.is_trained = True

    @_training
    def _mlp(self):
        self.cls.fit(self.accumulative_samples, self.accumulative_targets)
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

    def predict(self, data):  # type: (Trainer) -> None
        if self.is_trained and not self._is_training:
            # print(len(data))
            data = np.array(data).reshape(1, -1)
            prediction = self.cls.predict(data)
            print(prediction)
            self.prediction.on_next(prediction[0])

    def close(self):  # type: (Trainer) -> None
        self._is_open = False
        sleep(0.5)
        if len(self.training_summary) > 0:
            with open('./trainer_summary.json', 'r') as file:
                saved_data = json.loads(file.read())
                saved_data.append(self.training_summary)
                data_to_save = json.dumps(saved_data)
            with open('./trainer_summary.json', 'w+') as file:
                file.write(data_to_save)
        for subscription in self.subscriptions:
            try:
                subscription.dispose()
            except DisposedException:
                pass
