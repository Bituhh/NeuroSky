from msvcrt import kbhit, getch
from threading import Thread

from neurosky import Connector


class KeyHandler(object):
    def __init__(self):  # type: (KeyHandler) -> None
        self.keys = []  # type: List[Dict[str, Any]]

    def add_key(self, key, event):  # type: (KeyHandler, Any, Any) -> None
        self.keys.append({'key': ord(key), 'event': event})  # type: (Union[str, bytes, bytearray]) -> int

    def start(self):  # type: (KeyHandler) -> None
        Thread(target=self._run())

    def _run(self):  # type: (KeyHandler) -> None
        while True:
            if kbhit():
                key_pressed = ord(getch())
                if key_pressed is 27:
                    'Exiting'
                    break
                else:
                    for key in self.keys:
                        if key['key'] is key_pressed:
                            key['event']()


def key_handler():
    while True:
        if kbhit():
            key = getch()
            # print(key)
            if ord(key) is 27:
                print('Quitting')
                print(key)
                break
            elif ord(key) is 119:
                print('up')
                print(chr(ord(key)))
            elif ord(key) is 100:
                print('Right')
                print(key)
            elif ord(key) is 115:
                print('down')
                print(key)
            elif ord(key) is 97:
                print('Left')
                print(key)


if __name__ == '__main__':
    # Initializing key_handler
    # Thread(target=key_handler()).start()
    connector = Connector()
    connector.record('./data_t')

    # Creating neurosky constructors
    connector = Connector(debug=False, verbose=False)
    processor = Processor()
    trainer = Trainer()

    # Connecting async data handlers
    # connector.data.subscribe(processor.add_data)
    # processor.data.subscribe(trainer.add_data)

    # Closing neurosky
    # connector.close()
    # processor.close()
    # trainer.close()
