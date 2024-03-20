import time

from neurosky import Connector, Processor

connector = Connector(debug=True, verbose=True)
processor = Processor()

connector.data.subscribe(processor.add_data)
processor.data.subscribe(print)

time.sleep(10)
processor.close()
connector.close()
