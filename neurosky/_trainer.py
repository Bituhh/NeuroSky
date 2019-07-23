#!/usr/bin/env python3
from functools import wraps

try:
    from neurosky.utils import KeyHandler
    from neurosky._connector import Connector
    from neurosky._processor import Processor
except ModuleNotFoundError:
    from utils import KeyHandler
    from _connector import Connector
    from _processor import Processor

from threading import Thread
from time import sleep
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
            'RandomForest': RandomForestClassifier(n_estimators=10),
            'MLP': MLPClassifier(
                solver='lbfgs',
                hidden_layer_sizes=(100, 100, 100),
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
        self.samples = []
        self.targets = []
        self.accumulative_samples = []
        self.accumulative_targets = []
        # self.training_counter = 0

        # Prediction Params
        self.prediction_wait_time = 0.25
        self.current_data = []

        # Prediction initialiser
        # self.confidence_level = []
        self._identifiers = []
        # self._init_thread(target=self.predict)
        self._initialise_classifier(classifier_name)

    @staticmethod
    def _init_thread(target, args=()):
        Thread(target=target, args=args).start()

    def add_data(self, data):  # type: (Trainer, Any) -> None
        self.current_data = data
        print(data)

        if self._is_recording_data:
            self.samples.append(data[0])
            self.targets.append(self.current_training_target)
            self.accumulative_samples.append(data[0])
            self.accumulative_targets.append(self.current_training_target)
        else:
            self.predict()

    def _initialise_classifier(self, classifier_name):
        # try:
        initial_forward_data = np.load('./neurosky/training_initialiser/forward_processor_data.npy')
        initial_backward_data = np.load('./neurosky/training_initialiser/backward_processor_data.npy')
        initial_idle_data = np.load('./neurosky/training_initialiser/idle_processor_data.npy')
        # except:
            # print('Unable to load files')
        data_identifiers = [initial_forward_data, initial_backward_data, initial_idle_data]
        for data_identifier in data_identifiers:
            for i, data in enumerate(data_identifier):
                print(np.array(data).shape)
                self.accumulative_samples.append(data[0])
                self.accumulative_targets.append(i)
                self.samples.append(data[0])
                self.targets.append(i)
        print(np.array(self.samples).shape)
        print('Starting initial training...')
        if classifier_name == 'RandomForest':
            self._init_thread(self._random_forest.__wrapped__, args=(self,))
        elif classifier_name == 'MLP':
            self._init_thread(self._mlp.__wrapped__, args=(self,))
        print('Finalising initial training...')

    def train(self, target):  # type: (Trainer, Any) -> None
        # Determining target
        for identifier in self._identifiers:
            if identifier['name'] is target:
                self.current_training_target = identifier['target']
                identifier['training_count'] += 1
                self._update_identifiers()
                break

        if self.classifier == 'RandomForest':
            self._init_thread(target=self._random_forest)
        elif self.classifier == 'MLP':
            self._init_thread(target=self._mlp)

    def _training_decorator(func):
        @wraps(func)
        def wrapper(self):
            # Set training flag and status
            self.training_status.on_next('Training for {0}...'.format(self.current_training_target))
            self._is_training = True
            sleep(self.training_wait_time)
            self.training_status.on_next('Recording data...')
            self.samples = []
            self.targets = []
            self._is_recording_data = True
            sleep(self.recording_time)
            self._is_recording_data = False
            self.training_status.on_next('Fitting data...')
            func(self)
            self._is_training = False
            self.is_trained = True
            self.training_status.on_next('Training Complete')
        return wrapper

    @_training_decorator
    def _random_forest(self):
        self.cls.n_estimators += 1
        self.cls.fit(self.accumulative_samples, self.accumulative_targets)

    @_training_decorator
    def _mlp(self):
        print('mlp')
        self.cls.fit(self.samples, self.targets)

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
        self.trainer = Trainer(classifier_name='RandomForestq')

        self.connector.data.subscribe(self.processor.add_data)
        self.processor.data.subscribe(self.trainer.add_data)

        self.IDENTIFIER_FORWARD = self.trainer.add_identifier('forward')
        self.IDENTIFIER_DOWN = self.trainer.add_identifier('backward')
        self.IDENTIFIER_IDLE = self.trainer.add_identifier('idle')

        self.key_handler = KeyHandler()
        self.key_handler.add_key_event(key='q', event=self.close_all)
        self.key_handler.add_key_event(key='1', event=self.record, identifier_name=self.IDENTIFIER_FORWARD)
        self.key_handler.add_key_event(key='2', event=self.record, identifier_name=self.IDENTIFIER_DOWN)
        self.key_handler.add_key_event(key='3', event=self.record, identifier_name=self.IDENTIFIER_IDLE)
        self.key_handler.add_key_event(key='p', event=self.trainer.predict)
        self.key_handler.start()

    def record(self, identifier_name):
        self.connector.record('./neurosky/training_initialiser/' + identifier_name + '_connector_data')
        self.processor.record('./neurosky/training_initialiser/' + identifier_name + '_processor_data')

    def close_all(self):
        self.connector.close()
        self.processor.close()
        self.trainer.close()
        self.key_handler.stop()


if __name__ == '__main__':
    test = _TestTrainer()
