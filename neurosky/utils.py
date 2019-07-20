from msvcrt import kbhit, getch
from threading import Thread


class KeyHandler:
    def __init__(self):  # type: (KeyHandler) -> None
        self._events = []
        self.thread = Thread(target=self._run)
        self._is_running = False

    def add_key_event(self, key, event, **kwargs):  # type: (KeyHandler, Any, Any, Tuple[Any, ...]) -> None
        self._events.append({'key': ord(key), 'event': event, 'args': kwargs})

    def start(self):  # type: (KeyHandler) -> None
        self._is_running = True
        self.thread.start()

    def _run(self):  # type: (KeyHandler) -> None
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

    def stop(self):
        self._is_running = False
