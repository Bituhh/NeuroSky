from neurosky import Connector, Processor, KeyHandler

key_handler: KeyHandler = KeyHandler()
with Connector(verbose=True) as connector:  # Connector assumes debug and verbose to be False.
    with Processor() as processor:
        connector.data.subscribe(processor.add_data)  # using named method.
        processor.data.subscribe(lambda x: print(x))  # using anonymous lambda method.
        # By setting the halt_mode to True, you ensure the program won't quit until the key 'q' is pressed.
        key_handler.start(True)
        # Any code after this won't execute unless the key 'q' is pressed.
        print('should only execute after the key "q" is pressed')
