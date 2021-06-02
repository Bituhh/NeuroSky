import os
import winsound

import numpy as np

try:
    from neurosky._processor import Processor
    from neurosky._new_trainer import Trainer
except ModuleNotFoundError:
    # noinspection PyUnresolvedReferences
    from _processor import Processor
    # noinspection PyUnresolvedReferences
    from _new_trainer import Trainer

classifier_name = 'KNN'  # 'MLP' || 'RandomForest' || 'SVC' || 'KNN' || 'AdaBoost'
split_by = 1

dir_size = int(len(os.listdir('./motor_imagery_data')) / 2)
data_batch = []
for i in range(int(dir_size)):
    data_points = np.load('./motor_imagery_data/right_arm_' + str(i + 1) + '.npy')
    for data in np.array_split(data_points, split_by):
        data_batch.append([data, 0])
    data_points = np.load('./motor_imagery_data/left_arm_' + str(i + 1) + '.npy')
    for data in np.array_split(data_points, split_by):
        data_batch.append([data, 1])

# print(len(data_batch))

processor = Processor(batch_mode=True)


def process(data, pca=False, ica=False):
    processed_data = []
    for x in data:
        processor.fft(x)
        processed_data.append(processor.processed_data)
    if pca:
        # print(np.array(processed_data).shape)
        processed_data = processor.pca(processed_data)
        # print(np.array(processed_data).shape)
    if ica:
        processed_data = processor.ica(processed_data)
    return processed_data


def split_x_y(data):
    X = []
    y = []
    for x in data:
        X.append(x[0])
        y.append(x[1])
    return X, y


# accuracy = []
# print('Raw')
# for _ in range(3):
#     np.random.shuffle(data_batch)
#     train_batch, test_batch = np.split(np.array(data_batch), [int(0.8 * len(data_batch))])
#
#     X_train, y_train = split_x_y(train_batch)
#
#     X_test, y_test = split_x_y(test_batch)
#
#     trainer = Trainer(classifier_name=classifier_name)  # 'MLP' || 'RandomForest' || 'SVC' || 'KNN' || 'AdaBoost'
#     trainer.add_data(process(X_train), y_train)
#     trainer._train()
#     score = trainer.cls.score(process(X_test), y_test)
#     print(score)
#     accuracy.append(score)
#
# print(np.mean(accuracy))
# print('PCA')
# accuracy = []
# for _ in range(20):
#     np.random.shuffle(data_batch)
#     train_batch, test_batch = np.split(np.array(data_batch), [int(0.8 * len(data_batch))])
#
#     X_train, y_train = split_x_y(train_batch)
#
#     X_test, y_test = split_x_y(test_batch)
#
#     trainer = Trainer(classifier_name=classifier_name)  # 'MLP' || 'RandomForest' || 'SVC' || 'KNN' || 'AdaBoost'
#     trainer.add_data(process(X_train, pca=True, ica=False), y_train)
#     trainer._train()
#     a = process(X_test, pca=True, ica=False)
#     score = trainer.cls.score(a, y_test)
#     # print(score)
#     accuracy.append(score)

# print('ICA')
# accuracy = []
# for _ in range(20):
#     np.random.shuffle(data_batch)
#     train_batch, test_batch = np.split(np.array(data_batch), [int(0.8 * len(data_batch))])
#
#     X_train, y_train = split_x_y(train_batch)
#
#     X_test, y_test = split_x_y(test_batch)
#
#     trainer = Trainer(classifier_name=classifier_name)  # 'MLP' || 'RandomForest' || 'SVC' || 'KNN' || 'AdaBoost'
#     trainer.add_data(process(X_train, pca=False, ica=True), y_train)
#     trainer._train()
#
#     score = trainer.cls.score(process(X_test, pca=False, ica=True), y_test)
#     # print(score)
#     accuracy.append(score)

print('PCA & ICA')
accuracy = []
for _ in range(20):
    np.random.shuffle(data_batch)
    train_batch, test_batch = np.split(np.array(data_batch), [int(0.8 * len(data_batch))])

    X_train, y_train = split_x_y(train_batch)

    X_test, y_test = split_x_y(test_batch)

    trainer = Trainer(classifier_name=classifier_name)  # 'MLP' || 'RandomForest' || 'SVC' || 'KNN' || 'AdaBoost'
    trainer.add_data(process(X_train, pca=True, ica=True), y_train)
    trainer._train()

    score = trainer.cls.score(process(X_test, pca=True, ica=True), y_test)
    print(score)
    accuracy.append(score)
print('Mean Accuracy:\n', np.mean(accuracy))
print('Highest Value:\n', np.max(accuracy))
winsound.Beep(500, 100)
