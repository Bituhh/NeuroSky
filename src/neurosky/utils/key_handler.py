from msvcrt import kbhit, getch
from threading import Thread
from typing import Callable, Any


class KeyHandler:
    def __init__(self) -> None:
        self._events: list[dict] = [{'key': ord('q'), 'event': self.stop, 'args': ()}]
        self.thread: Thread = Thread(target=self._run)
        self._is_running: bool = False

    def add_key_event(self, key: str, event: Callable, **kwargs: tuple[Any, ...]) -> None:
        self._events.append({'key': ord(key), 'event': event, 'args': kwargs})

    def start(self, halt_mode: bool = False) -> None:
        """Starts key handler

        :keyword halt_mode -- If set to True the program will halt at the point in which it was called waiting for
        the 'quit' (q) event.
        """
        self._is_running = True
        if halt_mode:
            self._run()
        else:
            self.thread.start()

    def _run(self) -> None:
        while self._is_running:
            if kbhit():
                key_pressed = ord(getch())
                for _event in self._events:
                    if _event['key'] is key_pressed:
                        if _event['args']:
                            print(_event['args'])
                            _event['event'](**_event['args'])
                        else:
                            _event['event']()

    def stop(self) -> None:
        self._is_running = False


if __name__ == '__main__':
    key_handler = KeyHandler()
    key_handler.start()
    print('Should be holding')
