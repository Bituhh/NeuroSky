import os
from threading import Thread
from time import time, sleep
from winsound import Beep
import numpy as np
from rx.operators import take_until_with_time

try:
    from neurosky.utils import KeyHandler
    from neurosky._connector import Connector
    from neurosky._processor import Processor
    from neurosky._new_trainer import Trainer
    from neurosky._status_manager import StatusManager
except ModuleNotFoundError:
    # noinspection PyUnresolvedReferences
    from utils import KeyHandler
    # noinspection PyUnresolvedReferences
    from _connector import Connector
    # noinspection PyUnresolvedReferences
    from _processor import Processor
    # noinspection PyUnresolvedReferences
    from _new_trainer import Trainer
    # noinspection PyUnresolvedReferences
    from _status_manager import StatusManager


def _init_thread(target, args=()):
    Thread(target=target, args=args).start()


class _Tester:
    def __init__(self):
        # initialize
        # record
        # process with recorded data
        # train

        self.counter = 0
        self.signal_status = 'Poor Signal'
        self.is_prediction_mode = False
        self.data_to_predict = []

        # Initializing
        self.status_manager = StatusManager()
        self.status_manager.update_status('Initializing...')
        # self.connector = Connector(debug=False, verbose=False)
        self.processor = Processor(batch_mode=True)
        self.trainer = Trainer(classifier_name='MLP')  # 'MLP' || 'RandomForest' || 'SVC' || 'KNN' || 'AdaBoost'

        # self.connector.poor_signal_level.subscribe(self.check_poor_level)

        self.IDENTIFIER_RIGHT_ARM = self.status_manager.add_identifier('right_arm')
        self.IDENTIFIER_LEFT_ARM = self.status_manager.add_identifier('left_arm')
        self.IDENTIFIER_IDLE = self.status_manager.add_identifier('idle')

        # self.key_handler = KeyHandler()
        # self.key_handler.add_key_event(key='q', event=self.close_all)
        # self.key_handler.add_key_event(key=chr(96), event=self.train, identifier=self.IDENTIFIER_RIGHT_ARM)
        # self.key_handler.add_key_event(key=chr(45), event=self.train, identifier=self.IDENTIFIER_LEFT_ARM)
        # self.key_handler.add_key_event(key='c', event=self._init_training)
        # self.key_handler.add_key_event(key='p', event=self.toggle_prediction)
        # self.key_handler.add_key_event(key='3', event=self.train, identifier=self.IDENTIFIER_IDLE)
        # self.key_handler.add_key_event(key='p', event=self.trainer.predict)
        # self.key_handler.start()

        self._init_training()
        # self.connector.data.pipe(take_until_with_time(10)).subscribe(
        #     observer=self.data_to_predict.append,
        #     on_error=print,
        #     on_completed=self.recursive_predict
        # )
        # self.trainer.prediction.subscribe(self.status_manager.predicted_identifier)

    def recursive_predict(self):
        if self.is_prediction_mode:
            self.processor.add_data_batch(self.data_to_predict)
            # X = self.processor.pca(self.processor.processed_data.reshape(1, -1))
            self.trainer.predict(self.data_to_predict)
        self.connector.data.pipe(take_until_with_time(1)).subscribe(
            observer=self.loop_data,
            on_error=print,
            on_completed=self.recursive_predict
        )

    def loop_data(self, data):
        self.data_to_predict.pop(0)
        self.data_to_predict.append(data)

    def toggle_prediction(self):
        self.is_prediction_mode = not self.is_prediction_mode

    def _init_training(self):
        dir_size = int(len(os.listdir('./motor_imagery_data')) / 2)
        split = int(dir_size/3)*2
        X = []
        y = []
        for i in range(split):
            right_arm_data = np.load('./motor_imagery_data/right_arm_' + str(i + 1) + '.npy')
            self.processor.add_data_batch(right_arm_data)
            X.append(self.processor.processed_data)
            y.append(self.IDENTIFIER_RIGHT_ARM)
            left_arm_data = np.load('./motor_imagery_data/left_arm_' + str(i + 1) + '.npy')
            self.processor.add_data_batch(left_arm_data)
            X.append(self.processor.processed_data)
            y.append(self.IDENTIFIER_LEFT_ARM)
        X = self.processor.pca(X)
        self.trainer.add_data(X, y)
        self.trainer._train()
        X_test = []
        y_test = []
        for i in range(split, dir_size):
            right_arm_data = np.load('./motor_imagery_data/right_arm_' + str(i + 1) + '.npy')
            self.processor.add_data_batch(right_arm_data)
            X_test.append(self.processor.processed_data)
            y_test.append(self.IDENTIFIER_RIGHT_ARM)
            left_arm_data = np.load('./motor_imagery_data/left_arm_' + str(i + 1) + '.npy')
            self.processor.add_data_batch(left_arm_data)
            X_test.append(self.processor.processed_data)
            y_test.append(self.IDENTIFIER_LEFT_ARM)
        X_test = self.processor.pca(X_test)
        self.trainer.add_data(X_test, y_test)
        print(self.trainer.cls.score(self.trainer.samples, self.trainer.targets))
        self.trainer.clear_data()
        # self.close_all()

    def train(self, identifier):
        self.status_manager.update_status('Preparing...')
        start_time = time()
        while time() - start_time < 3:
            pass
        Beep(500, 100)
        for _ in range(5):
            self.status_manager.update_status('Recording...')
            self.connector.record('./motor_imagery_data/' + self.status_manager.next_label(identifier))
            self.connector.await_recording()
        Beep(500, 100)
        Beep(500, 100)
        # self.status_manager.update_status('Pre-processing...')
        # self.processor.add_data_batch(self.connector.recorded_data)
        # self.status_manager.update_status('Training...')
        # self.trainer.add_data(self.processor.processed_data[0])
        # self.trainer.train(identifier)

    def check_poor_level(self, level):
        if level > 0:
            if self.signal_status is not 'Poor Signal...':
                print('Poor Signal...')
                self.signal_status = 'Poor Signal...'
        else:
            if self.signal_status is not 'Good Signal':
                print('Good Signal')
                self.signal_status = 'Good Signal'

    def close_all(self):
        self.trainer.close()
        self.processor.close()
        # self.connector.close()
        self.status_manager.close()
        # self.key_handler.stop()


if __name__ == '__main__':
    total_size = 0
    for i in range(int(len(os.listdir('./motor_imagery_data')) / 2)):
        right_arm_data = np.load('./motor_imagery_data/right_arm_' + str(i + 1) + '.npy')
        print(len(right_arm_data))
        total_size += len(right_arm_data)
        left_arm_data = np.load('./motor_imagery_data/left_arm_' + str(i + 1) + '.npy')
        print(len(left_arm_data))
        total_size += len(left_arm_data)
    print(total_size)
    #
    # tester = _Tester()
    # tester.status_manager.status.subscribe(print)
