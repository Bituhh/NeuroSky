import time

from neurosky import Connector, Processor

connector = Connector(verbose=True)
processor = Processor()

connector.start()  # Start the connector thread, which will start the data stream.

connector.data.subscribe(processor.add_data)
processor.data.subscribe(print)

time.sleep(10)
processor.close()
connector.close()
