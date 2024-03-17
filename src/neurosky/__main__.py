from neurosky import Connector
from neurosky.utils import KeyHandler


def main():
    key_handler = KeyHandler()
    with Connector() as connector:
        connector.data.subscribe(lambda x: print(x))
        key_handler.start(halt_mode=True)


if __name__ == "__main__":
    main()
