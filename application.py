#!/usr/bin/env python3

import sys
import numpy as np
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QLogValueAxis, QValueAxis
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from neurosky import Connector, Processor



class Linker(QObject):
    raw = pyqtSignal(int)
    fft = pyqtSignal(np.ndarray)
    poor_signal_level = pyqtSignal(int)
    sampling_rate = pyqtSignal(int)

    def __init__(self):
        QObject.__init__(self)
        self.connector = Connector(debug=True, verbose=False)
        self.processor = Processor()
        self.connector.data.subscribe(self._new_connector_data)
        self.connector.poor_signal_level.subscribe(self.poor_signal_level.emit)
        self.connector.sampling_rate.subscribe(self.sampling_rate.emit)
        self.processor.data.subscribe(self.fft.emit)

    def _new_connector_data(self, data):
        self.processor.add_data(data)
        self.raw.emit(data)

    def close(self):
        self.connector.close()
        self.processor.close()


class Display(QWidget):
    def __init__(self, debug=False, verbose=False, link=Linker()):
        QWidget.__init__(self) # flags=Qt.CustomizeWindowHint | Qt.WindowTitleHint
        self._DEBUG = debug
        self._VERBOSE = verbose
        self._link = link
        self.setWindowTitle("NeuroSky GUI")
        self.resize(1400, 1000)

        # Indicators
        self._raw_data_indicator = self._create_indicator('Raw Data:')
        self._poor_level_indicator = self._create_indicator('Poor Level Signal:')
        self._sample_rate_indicator = self._create_indicator('Sample Rate:')
        self._prediction_indicator = self._create_indicator('Prediction:')
        self._training_status_indicator = self._create_indicator('Training Status:')

        # Initializing layout
        self.main_page()

        # Series
        self._x_axis = 0
        self._connect_data()

        self._raw_w_index = 1
        self._processed_w_index = 1
        self._raw_s_index = 1
        self._processed_s_index = 1
        self.is_recording_mode = False
        # self.raw_x = 0
        # self.raw_y = 0
        # self.fft_x = []
        # self.fft_y = []

    def main_page(self):  # type: (Display) -> None
        # Top Layout
        top_left_layout = QVBoxLayout()
        top_left_layout.addLayout(self._raw_data_indicator['layout'])
        top_left_layout.addLayout(self._poor_level_indicator['layout'])
        top_left_layout.addLayout(self._sample_rate_indicator['layout'])

        top_right_layout = QVBoxLayout()
        top_right_layout.addWidget(self._get_connector_chart(), alignment=Qt.AlignCenter)
        # top_right_layout.setStretchFactor(self._get_connector_chart(), 1)

        top_layout = QHBoxLayout()
        top_layout.addLayout(top_left_layout)
        top_layout.addLayout(top_right_layout)

        # Bottom Layout
        bottom_left_layout = QVBoxLayout()
        bottom_left_layout.addLayout(self._prediction_indicator['layout'])
        bottom_left_layout.addLayout(self._training_status_indicator['layout'])

        bottom_right_layout = QVBoxLayout()
        bottom_right_layout.addWidget(self._get_processor_chart(), alignment=Qt.AlignCenter)

        bottom_layout = QHBoxLayout()
        bottom_layout.addLayout(bottom_left_layout)
        bottom_layout.addLayout(bottom_right_layout)

        # Outer Layout
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(top_layout)
        outer_layout.addLayout(bottom_layout)

        # Set Layout
        self.setLayout(outer_layout)

        # Recorded Data

    @staticmethod
    def _create_indicator(label):  # type: (Any) -> Dict[str, Union[QHBoxLayout, QLabel]]
        layout = QHBoxLayout()
        display_widget = QLabel(label)
        layout.addWidget(display_widget, alignment=Qt.AlignCenter)
        label_widget = QLabel('Initializing...')
        layout.addWidget(label_widget, alignment=Qt.AlignCenter)
        return {'layout': layout, 'display': display_widget, 'label': label_widget}

    def _get_connector_chart(self):  # type: (Display) -> QChartView
        # Create pen
        pen = QLineSeries().pen()
        pen.setColor(Qt.blue)
        pen.setWidthF(1)

        # Series
        self._connector_series = QLineSeries()
        self._connector_series.setPen(pen)
        self._connector_series.useOpenGL()

        # Chart
        self._connector_chart = QChart()
        self._connector_chart.legend().hide()
        self._connector_chart.addSeries(self._connector_series)
        self._connector_chart.createDefaultAxes()
        self._connector_chart.axisX().setMax(100)
        self._connector_chart.axisX().setMin(0)
        self._connector_chart.axisY().setMax(150)
        self._connector_chart.axisY().setMin(-150)

        # Chart View
        view = QChartView(self._connector_chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet('margin: 0px; height: 250%; width: 400%;')
        return view

    def _get_processor_chart(self):  # type: (Display) -> QChartView
        # Create pen
        pen = QLineSeries().pen()
        pen.setColor(Qt.red)
        pen.setWidthF(1)

        # Series
        self._processor_series = QLineSeries()
        self._processor_series.setPen(pen)
        self._processor_series.useOpenGL()

        # Chart
        self._processor_chart = QChart()
        self._processor_chart.legend().hide()
        self._processor_chart.addSeries(self._processor_series)
        self._processor_chart.createDefaultAxes()
        self._processor_chart.axisX().setMax(100)
        self._processor_chart.axisX().setMin(0)
        self._processor_chart.axisY().setMax(5000)
        self._processor_chart.axisY().setMin(0)

        self._processor_x_axis = QValueAxis()
        # self._processor_x_axis.setTitleText("Data point")
        self._processor_x_axis.setLabelFormat('%i')
        # self._processor_x_axis.setTickCount(self._processor_series.count())
        self._processor_chart.setAxisX(self._processor_x_axis, self._processor_series)

        self._processor_y_axis = QLogValueAxis()
        # self._processor_y_axis.setTitleText('Values')
        self._processor_y_axis.setLabelFormat('%g')
        self._processor_y_axis.setBase(8)
        # self._processor_y_axis.setMinorTickCount(-1)
        # self._processor_chart.setAxisY(self._processor_y_axis)

        # self._processor_series.attachAxis(self._processor_x_axis)
        # self._processor_series.attachAxis(self._processor_y_axis)

        # Chart View
        view = QChartView(self._processor_chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet('margin: 0px; height: 250%; width: 400%;')
        return view

    def _connect_data(self):  # type: (Display) -> None
        self._link.raw.connect(self._add_connector_data)
        self._link.poor_signal_level.connect(lambda level: self._poor_level_indicator['label'].setText(str(level)))
        self._link.sampling_rate.connect(lambda rate: self._sample_rate_indicator['label'].setText(str(rate)))
        self._link.fft.connect(self._add_processor_data)

    @pyqtSlot(int)
    def _add_connector_data(self, data):  # type: (Display, Any) -> Optional[Any]
        self._raw_data_indicator['label'].setText(str(data))
        self._connector_series.append(self._x_axis, data)
        if self._connector_series.count() >= 100:
            self._connector_series.clear()
            self._x_axis = 0
        else:
            self._x_axis += 1

    @pyqtSlot(np.ndarray)
    def _add_processor_data(self, data):  # type: (Display, Any) -> Optional[Any]
        self._processor_series.clear()
        x_axis = data[0]
        y_axis = data[1]
        for i in range(len(x_axis)):
            self._processor_series.append(x_axis[i], y_axis[i])

    def keyPressEvent(self, event):  # type: (Display, {key}) -> None
        key = event.key()
        if key == Qt.Key_Escape:
            self._link.close()
            self.close()
        elif key == Qt.Key_W:
            self._link.connector.record('./data/raw_data/w_' + str(self._raw_w_index))
            self._link.processor.record('./data/processed_data/w_' + str(self._processed_w_index))
            self._raw_w_index += 1
            self._processed_w_index += 1
            print('w')
        elif key == Qt.Key_S:
            self._link.connector.record('./data/raw_data/s_' + str(self._raw_s_index))
            self._link.processor.record('./data/processed_data/s_' + str(self._processed_s_index))
            self._raw_s_index += 1
            self._processed_s_index += 1
            print('s')
        elif key == Qt.Key_Space:
            self.is_recording_mode = not self.is_recording_mode
            print(self.is_recording_mode)
        else:
            print(key)

    def closeEvent(self, event):
        self.close()
        self._link.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = Display(debug=True, verbose=False, link=Linker())
    ui.show()
    sys.exit(app.exec_())
