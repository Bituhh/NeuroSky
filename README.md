# NeuroSky

This project is part of my Final 3rd Year Project.

## Instructions:

The library is split into 4 sections:

- `neurosky.Connector`
    - The connector reaches to the ThinkGear Connector (NeuroSky Device) utilising the socket library, and returns the
      raw output from the 'data' Observable.
      `connector = Connector(debug=False, verbose=False)`
- `neurosky.Processor`
    - The processor transforms the raw_data into fft_data. `processor = Processor()`
- `neurosky.Trainer` **REMOVE as of version 1.0.0 please see tag for version 0.0.1**
    - It trains the device utilising Random Forrest. `trainer = Trainer()`
- `neurosky.utils.KeyHandler`
    - Used to handle key events to call different functionality.

The whole project is designed in a reactive programming style by utilising the RxPy library to create Observables and
Subjects. Both the Connector and Processor contains a Subject labeled `data` in which you are able `subscribe()` to any
changes.

## Installation

Clone the repository and install the requirements.
```bash
git clone https://github.com/Bituhh/NeuroSky.git
cd NeuroSky

# Install the requirements
pip install -r requirements.txt
```

Ensure that the following executable is running `ThinkGear_Connector/ThinkGear Connector.exe`.
This is the ThinkGear Connector that will be used to connect to the NeuroSky device.

Once you connect the device via Bluetooth.
Run the demo to ensure everything is working as expected.
```bash
python ./src/demo-1.py
```

## Examples

### Method 1 - Automatic releasing resources using "with" keyword

```python
from neurosky import Connector, Processor
from neurosky.utils import KeyHandler

key_handler: KeyHandler = KeyHandler()
with Connector() as connector:  # Connector assumes debug and verbose to be False.
    with Processor() as processor:
        connector.data.subscribe(processor.add_data)  # using named method.
        processor.data.subscribe(lambda x: print(x))  # using anonymous lambda method. 
        # By setting the halt_mode to True, you ensure the program won't quit until the key 'q' is pressed.
        key_handler.start(True)
        # Any code after this won't execute unless the key 'q' is pressed.
        print('should only execute after the key "q" is pressed')
```

### Method 2 - Manually handling resources releases

```python
from time import sleep
from neurosky import Connector, Processor
from neurosky.utils import KeyHandler

key_handler = KeyHandler()
connector = Connector()
processor = Processor()

connector.start()  # Start the connector thread, which will start the data stream.

# Calling async subscribers.
connector.data.subscribe(processor.add_data)  # using named method.
processor.data.subscribe(lambda data: print(data))

print('do action that will take some time to finish')
sleep(10)

# Always close at end of application.
# It releases resource from the RxPy subscriptions.
connector.close()
processor.close()
# Class will have to be reassigned if you wish to subscribe after calling close.
```

## Contact Info:

For any further details on this project feel free to contact me at:

Email: victor@bituhh.com

LinkedIn: [Victor Oliveira](https://www.linkedin.com/in/vcoliveira)

Thank you.
