#!/usr/bin/env python3

import threading

from neurosky._connector import Connector
from neurosky._processor import Processor
from time import sleep, time
from sklearn.ensemble import RandomForestClassifier
from rx.subject import Subject


class Trainer(object):
    def __init__(self,type):
        # Classifier Initializer
        self.cls = RandomForestClassifier(n_estimators=100)

        # disposal handler
        self.subscriptions = []

        # Observables and Subjects
        self.prediction = Subject()
        self.subscriptions.append(self.prediction)

        # Training Params
        self.training_wait_time = 3
        self.recording_time = 3
        self.is_recording_data = False
        self.is_previously_trained = False
        self.is_training = False
        self.current_training_target = None
        self.sample = []
        self.target = []
        # self.training_counter = 0

        # Prediction Params
        self.prediction_wait_time = 0.25
        self.current_data = []

        # Prediction Initializer
        # self.confidence_level = []
        self._init_thread(target=self.predict)

        '''
        Handling data steps:
        wait a time interval
        record data for a set time interval
        score data if previously trained
        train on data set.
        '''

    @staticmethod
    def _init_thread(target, args=()):
        threading.Thread(target=target, args=args).start()

    def add_data(self, data):
        self.current_data = data
        if self.is_recording_data:
            self.sample.append(self.current_data)
            self.target.append(self.current_training_target)

    def train(self, target):
        self.is_training = True
        self.current_training_target = target
        sleep(self.training_wait_time)
        self.is_recording_data = True
        sleep(self.recording_time)
        self.is_recording_data = False
        # score previous training
        # if self.is_previously_trained:
        #     self.confidence_level.append(
        #         [self.cls.score(recorded_data, recorded_target), self.training_counter, int(target)])
        #     print(self.confidence_level[-1])
        #     has_confidence_level = True
        self.cls.n_estimators += 1
        training_start_time = time()
        self.cls.fit(self.sample, self.target)
        print(training_start_time)
        self.is_training = False
        # if has_confidence_level:
        #     self.confidence_level[-1].append(time() - training_start_time)
        #     print(self.confidence_level[-1][2])
        # print('done fitting')
        # self.is_trained = True
        # self.prediction_status = 'Ready...'
        # self.training_counter += 1

    def predict(self):
        if self.is_previously_trained and not self.is_training:
            try:
                if self.cls.predict(self.current_data)[0] == 0:
                    self.prediction = 'Arms Up'
                else:
                    self.prediction = 'Arms Down'
                sleep(self.prediction_wait_time)
            except:
                print('An error occurred on prediction, prediction not performed!')

    def close(self):
        for subscription in self.subscriptions:
            subscription.dispose()


if __name__ == '__main__':
    connector = Connector(debug=True, verbose=False)
    processor = Processor()
    trainer = Trainer()

    connector.data.subscribe(processor.add_data)
    processor.data.subscribe(trainer.add_data)
    counter = 0

    connector.close()
    processor.close()
    trainer.close()
