# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
import socket
import time
import threading
import sys

import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

import arduino_interface

def autoconnect_to_arduino(stop_event = None):

    print("Waiting for Arduino")

    serial_ports = []
    arduino = None
    while (len(serial_ports) == 0):
        serial_ports = arduino_interface.find_arduino_ports()

        if (len(serial_ports) >= 1):
            serial_port = serial_ports[0]
            print("Port:", serial_port)
            arduino = arduino_interface.TwoChannelADC(serial_port)
            break

        if (stop_event is not None):
            if (stop_event.is_set()):
                break

        time.sleep(0.5)

    print("Arduino connected")

    return arduino

adc_data = []
adc_data_lock = None
adc_data_0 = []
adc_data_1 = []

curve1 = None
curve2 = None
win = None
timer = None

def arduino_worker(stop_event):
    """thread worker function"""

    print('Worker')

    global adc_data_lock, adc_data

    # auto connect to arduino
    arduino = autoconnect_to_arduino(stop_event)
    time.sleep(1)
    arduino.start_command()

    counter = 0
    while (not stop_event.is_set()):
        adc_vals = arduino.read_adc()
        if adc_vals is not None:
            data = (counter, adc_vals[0], adc_vals[1])

            adc_data_lock.acquire()
            adc_data += [data]
            adc_data_lock.release()

            counter += 1

    print ("worker exit")

#    arduino.close()

def update_plot():

   # print("update plot")

    global curve1, curve2, adc_data_lock, adc_data, adc_data_0, adc_data_1

    # lock and extract the adc data
    adc_data_lock.acquire()

    t = [x[0]/1000 for x in adc_data]
    a0 = [x[1] for x in adc_data]
    a1 = [x[2] for x in adc_data]

    adc_data = []
    adc_data_lock.release()

    adc_data_0 += a0
    adc_data_1 += a1

    #print("plotting", len(adc_data_1))
    curve1.setData(adc_data_0)
    curve2.setData(adc_data_1)

def setup_graphics(app):

    print("setup graphics")

    global curve1, curve2, win, timer

    win = pg.GraphicsWindow(title="Basic plotting examples")
    win.resize(1000,600)
    win.setWindowTitle('pyqtgraph example: Plotting')

    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)

    # add the main plot
    p = win.addPlot(title="ADC1")
    p.showGrid(x=True, y=True)
    p.setRange(xRange=[0, 45000], yRange=[0, 256])
    curve1 = p.plot(pen='y')
    curve2 = p.plot(pen='r')
    #data = np.random.normal(size=(10,1000))
    #ptr = 0

    timer = QtCore.QTimer()
    timer.timeout.connect(update_plot)
    timer.start(50)

    print("timer set")

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys

    # synchronization stuff
    adc_data_lock = threading.RLock()
    stop_event = threading.Event()

    # arduino handle thread
    arduino_thread = threading.Thread(target=arduino_worker, args = (stop_event,))
    arduino_thread.start()

    # execute the graphics
    app = QtGui.QApplication([])

    setup_graphics(app)

    print("executing app")

    #app.exec_()
    #if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    QtGui.QApplication.instance().exec_()

    print("app done")

    # stop the thread
    stop_event.set()
    arduino_thread.join()

    print("total done")

