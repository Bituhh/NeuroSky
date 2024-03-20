try:
    from .key_handler import KeyHandler
except ImportError:
    from key_handler import KeyHandler

__all__ = ['KeyHandler']
