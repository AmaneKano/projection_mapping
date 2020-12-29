# Projection Mapping Software with Micro-Manager

## Dependencies
Python 3.7~<br>
OpenCV for Python<br>
Python wx<br>
Arduino IDE<br>
[Micro-Manager](https://micro-manager.org)<br>

## Setup
1. Install Micro-Manager(https://micro-manager.org)
2. Make Micro-Maneger configuration file about camera in the Micro-Manager installed folder
3. Put files in the Micro-Manager installed folder 
4. Install wx and open cv for python
5. Install arduino IDE

## Usage
1. type bellow in Micro-Manager installed folder
```
pythonw main.py
```
2. choose Calibration mode and click in the window.
3. choose Test Calibration mode and verify the calibration. If you can see diference, try Calibration again.
4. choose Live mode and adjust your sample.
5. choose Set Position mode and decide position in the window.
6. edit csv files and adjust timing of illumination.
7. choose Rec mode and start recording.
