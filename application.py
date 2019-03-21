#!/usr/bin/env python3

import sys
import numpy
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QLogValueAxis
from PyQt5.QtGui import QPolygonF, QPainter
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QGridLayout, QVBoxLayout, QGroupBox, QWidget, QLabel
from PyQt5.QtCore import Qt, QObject, QTimer
from neurosky import NeuroSky


class Display(QWidget):
    def __init__(self, debug=False, plot_freq=False):
        QWidget.__init__(self)
        self.plot_freq = plot_freq
        self.get_series(0.5, Qt.blue)
        self.get_charts()
        self.get_chart_views()
        self.get_labels()
        self.get_grid_layout()
        self.setWindowTitle("NeuroSky GUI")
        self.resize(800, 600)
        # Initialises the sensor
        self.neuro = NeuroSky(debug=debug)
        # Links the values with the display
        self.connect_data()

        # desable the close botton on application
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        self.x = 0
        self.y = 0

    def keyPressEvent(self, event):
        key = event.key()
        if key == 16777216:
            print('Closing Program')
            self.neuro.CLOSED = True
            self.close()
            pass

    def get_grid_layout(self):
        self.outer_layout = QGridLayout()

        # Indicators
        self.outer_layout.addWidget(self.poor_signal_display, 0, 0)
        self.outer_layout.addWidget(self.poor_signal_label, 0, 1)
        self.outer_layout.addWidget(self.raw_eeg_display, 1, 0)
        self.outer_layout.addWidget(self.raw_eeg_label, 1, 1)

        # Charts
        self.outer_layout.addWidget(self.raw_chart_view, 0, 2, 2, 4)
        self.outer_layout.addWidget(self.fft_chart_view, 2, 2, 2, 4)

        # Prediction
        self.outer_layout.addWidget(self.prediction_display, 2, 0)
        self.outer_layout.addWidget(self.prediction_label, 2, 1)
        self.outer_layout.addWidget(self.prediction_display, 3, 0)
        self.outer_layout.addWidget(self.prediction_label, 3, 1)

        # Timer
        self.outer_layout.addWidget(self.timer_display, 4, 2)
        self.outer_layout.addWidget(self.timer_label, 4, 3)
        self.outer_layout.addWidget(self.counter_display, 4, 4)
        self.outer_layout.addWidget(self.counter_label, 4, 5)

        self.setLayout(self.outer_layout)

    def get_labels(self):
        self.poor_signal_display = QLabel('Poor Signal Level:')
        self.poor_signal_display.setAlignment(Qt.AlignBottom)
        self.poor_signal_label = QLabel('Initialising...')
        self.poor_signal_label.setAlignment(Qt.AlignBottom)

        self.raw_eeg_display = QLabel('Raw EEG:')
        self.raw_eeg_display.setAlignment(Qt.AlignTop)
        self.raw_eeg_label = QLabel('Initialising...')
        self.raw_eeg_label.setAlignment(Qt.AlignTop)

        self.prediction_display = QLabel('Predicted:')
        self.prediction_display.setAlignment(Qt.AlignCenter)
        self.prediction_label = QLabel('Initialising...')
        self.prediction_label.setAlignment(Qt.AlignCenter)

        self.timer_display = QLabel('Timer:')
        self.timer_display.setAlignment(Qt.AlignLeft)
        self.timer_label = QLabel('Initialising...')
        self.timer_label.setAlignment(Qt.AlignLeft)

        self.counter_display = QLabel('Counter:')
        self.counter_display.setAlignment(Qt.AlignLeft)
        self.counter_label = QLabel('Initialising...')
        self.counter_label.setAlignment(Qt.AlignLeft)

    def get_series(self, width, color):
        self.raw_series = QLineSeries()
        self.fft_series = QLineSeries()
        pen = self.raw_series.pen()
        pen.setColor(color)
        pen.setWidthF(width)
        self.raw_series.setPen(pen)
        self.fft_series.setPen(pen)

    def get_charts(self):
        self.raw_chart = QChart()
        self.fft_chart = QChart()
        self.raw_chart.legend().hide()
        self.fft_chart.legend().hide()
        self.raw_chart.addSeries(self.raw_series)
        self.fft_chart.addSeries(self.fft_series)
        self.y_axis = QLogValueAxis()
        self.y_axis.setLabelFormat('%g')
        self.y_axis.setBase(8)
        self.raw_chart.createDefaultAxes()
        self.fft_chart.addAxis(self.y_axis, Qt.AlignLeft)
        self.fft_series.attachAxis(self.y_axis)

    def get_chart_views(self):
        self.raw_chart_view = QChartView(self.raw_chart)
        self.fft_chart_view = QChartView(self.fft_chart)
        self.raw_chart_view.setRenderHint(QPainter.Antialiasing)
        self.fft_chart_view.setRenderHint(QPainter.Antialiasing)
        self.raw_chart_view.setAlignment(Qt.AlignCenter)
        self.fft_chart_view.setAlignment(Qt.AlignCenter)

    def connect_data(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.plot_frequency)
        self.timer.timeout.connect(self.plot_raw)
        self.timer.timeout.connect(self.add_label_data)
        self.timer.start()

    def add_label_data(self):
        self.poor_signal_label.setText(str(self.neuro.poor_signal_level))
        self.raw_eeg_label.setText(str(self.neuro.raw_data))

    def plot_raw(self):
        self.y = self.neuro.raw_data
        self.raw_series.append(self.x, self.y)
        if self.x >= 100:
            self.raw_chart.axisX().setMax(self.x)
            self.raw_chart.axisX().setMin(self.x - 100)
        else:
            self.raw_chart.axisX().setMax(100)
            self.raw_chart.axisX().setMin(0)
        self.raw_chart.axisY().setMax(1000)
        self.raw_chart.axisY().setMin(-1000)
        self.x += 1

    def plot_frequency(self):
        if len(self.neuro.fft_data) > 0:
            self.fft_series.clear()
            self.x = self.neuro.fft_data[0]
            self.y = self.neuro.fft_data[1]
            self.chart.axisX().setMax(100)
            self.chart.axisX().setMin(0)
            self.chart.axisY().setMax(5000)
            self.chart.axisY().setMin(-5000)
            for i in range(len(self.x)):
                self.fft_series.append(self.x[i], self.y[i])


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ui = Display(debug=True)

    ui.show()
    sys.exit(app.exec_())
