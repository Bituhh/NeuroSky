# #!/usr/bin/env python3
#
# from msvcrt import kbhit, getch
#
# import sys
# import numpy
# from PyQt5.QtChart import QChart, QChartView, QLineSeries, QLogValueAxis
# from PyQt5.QtGui import QPolygonF, QPainter
# from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QGridLayout, QVBoxLayout, QGroupBox, QWidget, QLabel
# from PyQt5.QtCore import Qt, QObject, QTimer
# from connector import Connector
#
#
# class Display(QWidget):
#     def __init__(self, debug=False, verbose=False):
#         QWidget.__init__(self)
#         self.get_series(0.5, Qt.blue)
#         self.get_charts()
#         self.get_chart_views()
#         self.get_labels()
#         self.get_grid_layout()
#         self.setWindowTitle("NeuroSky GUI")
#         self.resize(1400, 1000)
#
#         # Initialises the sensor
#         self.neuro = NeuroSky(debug=debug, verbose=verbose)
#         self.neuro.remove_blinks = True
#         self.blink_threshold = 150
#         # Links the values with the display
#         self.connect_data()
#
#         # desable the close botton on application
#         self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
#
#         self.raw_x = 0
#         self.raw_y = 0
#         self.fft_x = []
#         self.fft_y = []
#
#     def keyPressEvent(self, event):
#         key = event.key()
#         if key == 16777216:
#             print('Closing Program')
#             self.neuro.CLOSED = True
#             self.close()
#         elif key == 87:
#             self.neuro.train(target=0)
#             print('w')
#         elif key == 83:
#             self.neuro.train(target=1)
#             print('s')
#
#     def train(self, target):
#         self.timer = QTimer()
#
#         self.timer.start()
#
#         pass
#
#     def get_grid_layout(self):
#         self.outer_layout = QGridLayout()
#
#         # Indicators
#         self.outer_layout.addWidget(self.poor_signal_display, 0, 0)
#         self.outer_layout.addWidget(self.poor_signal_label, 0, 1)
#         self.outer_layout.addWidget(self.raw_eeg_display, 1, 0)
#         self.outer_layout.addWidget(self.raw_eeg_label, 1, 1)
#         self.outer_layout.addWidget(self.sampling_rate_display, 2, 0)
#         self.outer_layout.addWidget(self.sampling_rate_label, 2, 1)
#
#         # Charts
#         self.outer_layout.addWidget(self.raw_chart_view, 0, 2, 4, 4)
#         self.outer_layout.addWidget(self.fft_chart_view, 4, 2, 4, 4)
#         self.outer_layout.addWidget(self.confidence_view, 6, 0, 2, 2)
#         # Prediction
#         self.outer_layout.addWidget(self.prediction_display, 4, 0)
#         self.outer_layout.addWidget(self.prediction_label, 4, 1)
#         self.outer_layout.addWidget(self.prediction_status_display, 5, 0)
#         self.outer_layout.addWidget(self.prediction_status_label, 5, 1)
#
#         # Timer
#         self.outer_layout.addWidget(self.timer_display, 8, 2)
#         self.outer_layout.addWidget(self.timer_label, 8, 3)
#         self.outer_layout.addWidget(self.counter_display, 8, 4)
#         self.outer_layout.addWidget(self.counter_label, 8, 5)
#
#         self.setLayout(self.outer_layout)
#
#     def get_labels(self):
#         # Indicators
#         self.poor_signal_display = QLabel('Poor Signal Level:')
#         self.poor_signal_display.setAlignment(Qt.AlignBottom)
#         self.poor_signal_label = QLabel('Initialising...')
#         self.poor_signal_label.setAlignment(Qt.AlignBottom)
#         self.raw_eeg_display = QLabel('Raw EEG:')
#         self.raw_eeg_display.setAlignment(Qt.AlignTop)
#         self.raw_eeg_label = QLabel('Initialising...')
#         self.raw_eeg_label.setAlignment(Qt.AlignTop)
#         self.sampling_rate_display = QLabel('Sampling Rate:')
#         self.sampling_rate_display.setAlignment(Qt.AlignTop)
#         self.sampling_rate_label = QLabel('Initialising...')
#         self.sampling_rate_label.setAlignment(Qt.AlignTop)
#
#         # Prediction
#         self.prediction_display = QLabel('Predicted:')
#         self.prediction_display.setAlignment(Qt.AlignLeft)
#         self.prediction_label = QLabel('Initialising...')
#         self.prediction_label.setAlignment(Qt.AlignLeft)
#         self.prediction_status_display = QLabel('Prediction Status:')
#         self.prediction_status_display.setAlignment(Qt.AlignLeft)
#         self.prediction_status_label = QLabel('Initialising...')
#         self.prediction_status_label.setAlignment(Qt.AlignLeft)
#
#         # Timer
#         self.timer_display = QLabel('Timer:')
#         self.timer_display.setAlignment(Qt.AlignRight)
#         self.timer_label = QLabel('Initialising...')
#         self.timer_label.setAlignment(Qt.AlignLeft)
#         self.counter_display = QLabel('Counter:')
#         self.counter_display.setAlignment(Qt.AlignRight)
#         self.counter_label = QLabel('Initialising...')
#         self.counter_label.setAlignment(Qt.AlignLeft)
#
#     def get_series(self, width, color):
#         self.raw_series = QLineSeries()
#         pen = self.raw_series.pen()
#         pen.setColor(color)
#         pen.setWidthF(width)
#         self.raw_series.setPen(pen)
#
#         self.fft_series = QLineSeries()
#         self.fft_series.setPen(pen)
#
#         self.w_series = QLineSeries()
#         self.w_series.setPen(pen)
#
#         self.s_series = QLineSeries()
#         self.s_series.setPen(pen)
#
#     def get_charts(self):
#         self.raw_chart = QChart()
#         self.raw_chart.legend().hide()
#         self.raw_chart.addSeries(self.raw_series)
#         self.raw_chart.createDefaultAxes()
#
#         self.fft_chart = QChart()
#         self.fft_chart.legend().hide()
#         self.fft_chart.addSeries(self.fft_series)
#         self.fft_y_axis = QLogValueAxis()
#         self.fft_y_axis.setLabelFormat('%g')
#         self.fft_y_axis.setBase(8)
#         self.fft_chart.createDefaultAxes()
#         self.fft_chart.axisX().setMax(100)
#         self.fft_chart.axisX().setMin(0)
#         self.fft_chart.axisY().setMax(5000)
#         self.fft_chart.axisY().setMin(0)
#
#         self.confidence_chart = QChart()
#         self.confidence_chart.legend().hide()
#         self.confidence_chart.addSeries(self.w_series)
#         self.confidence_chart.addSeries(self.s_series)
#         self.confidence_chart.createDefaultAxes()
#         self.confidence_chart.axisY().setMax(100)
#         self.confidence_chart.axisY().setMin(0)
#         self.confidence_chart.axisX().setMin(0)
#
#         # self.fft_chart.addAxis(self.fft_y_axis, Qt.AlignLeft)
#         # self.fft_series.attachAxis(self.fft_y_axis)
#
#     def get_chart_views(self):
#         self.raw_chart_view = QChartView(self.raw_chart)
#         self.raw_chart_view.setRenderHint(QPainter.Antialiasing)
#         self.raw_chart_view.setAlignment(Qt.AlignCenter)
#
#         self.fft_chart_view = QChartView(self.fft_chart)
#         self.fft_chart_view.setRenderHint(QPainter.Antialiasing)
#         self.fft_chart_view.setAlignment(Qt.AlignCenter)
#
#         self.confidence_view = QChartView(self.confidence_chart)
#         self.confidence_view.setRenderHint(QPainter.Antialiasing)
#         self.confidence_view.setAlignment(Qt.AlignCenter)
#
#     def connect_data(self):
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.plot_frequency)
#         self.timer.timeout.connect(self.plot_raw)
#         self.timer.timeout.connect(self.plot_confidence)
#         self.timer.timeout.connect(self.add_label_data)
#         self.timer.start()
#
#     def add_label_data(self):
#         self.poor_signal_label.setText(str(self.neuro.poor_signal_level))
#         self.raw_eeg_label.setText(str(self.neuro.raw_data))
#         self.prediction_label.setText(str(self.neuro.prediction))
#         self.prediction_status_label.setText(str(self.neuro.prediction_status))
#         self.sampling_rate_label.setText(str(self.neuro._sampling_rate))
#         self.counter_label.setText(str(self.neuro.training_counter))
#
#     def plot_raw(self):
#         self.raw_y = self.neuro.raw_data
#         self.raw_series.append(self.raw_x, self.raw_y)
#         if self.raw_x >= 100:
#             self.raw_chart.axisX().setMax(self.raw_x)
#             self.raw_chart.axisX().setMin(self.raw_x - 100)
#         else:
#             self.raw_chart.axisX().setMax(100)
#             self.raw_chart.axisX().setMin(0)
#         self.raw_chart.axisY().setMax(150)
#         self.raw_chart.axisY().setMin(-150)
#         self.raw_x += 1
#
#     def plot_frequency(self):
#         if len(self.neuro.fft_data) > 0:
#             self.fft_series.clear()
#             self.fft_x = self.neuro.fft_data[0]
#             self.fft_y = self.neuro.fft_data[1]
#             for i in range(len(self.fft_x)):
#                 self.fft_series.append(self.fft_x[i], self.fft_y[i])
#
#     def plot_confidence(self):
#         self.w_series.clear()
#         self.s_series.clear()
#         self.confidence_chart.axisX().setMax(len(self.neuro.confidence_level))
#         for element in self.neuro.confidence_level:
#             if element[2] is 0:
#                 self.w_series.append(element[1], element[0] * 100)
#             elif element[2] is 1:
#                 self.s_series.append(element[1], element[0] * 100)
#
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#
#     ui = Display(debug=False, verbose=False)
#
#     ui.show()
#     sys.exit(app.exec_())
#
#
# # press to record after 3 sec, record for 10 then stop
# # def keypress_handler(self):
#     #     print('Press ESC to quit at any time!')
#     #     while not self.is_closed:
#     #         # if ESC key is press stop running and close socket
#     #         if kbhit():
#     #             key = ord(getch())
#     #             if key is 27:
#     #                 self.is_closed = True
#     #                 break