try:
    # Relative path import
    from .connector import Connector
except ImportError:
    # Absolute path import
    from neurosky.connector import Connector

try:
    # Relative path import
    from .processor import Processor
except ImportError:
    # Absolute path import
    from neurosky.processor import Processor

try:
    # Relative path import
    from .utils import KeyHandler
except ImportError:
    # Absolute path import
    from neurosky.utils import KeyHandler


__all__ = ['Connector', 'Processor', 'KeyHandler']
