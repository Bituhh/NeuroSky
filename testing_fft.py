from scipy.fftpack import fft, ifft
from neurosky import NeuroSky
from time import sleep


neuro = NeuroSky(debug=True, verbose=False)

while not neuro.CLOSED:
    # sleep(0.1)
    print(neuro.fft_data)
