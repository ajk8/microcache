import contextlib
import decorator
import logging
import time
from ._version import __version__, __version_info__  # flake8: noqa

logger = logging.getLogger(__name__)
_CACHE = {}


class MicrocacheOptions(object):
    def __init__(self):
        self.enabled = True
        self.debug = False


options = MicrocacheOptions()


def _set_log_level():
    """ Make sure that logging is respecting the debug setting """
    logger.setLevel(logging.DEBUG if options.debug else logging.INFO)


class MicrocacheItem(object):
    def __init__(self, value, ttl):
        self.value = value
        self.ttl = ttl
        self.timestamp = time.time()

    def is_expired(self):
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


def has(key):
    """ See if a key is in the cache

    >>> import microcache
    >>> microcache.has('has')
    False
    >>> microcache.upsert('has', 'now')
    >>> microcache.has('has')
    True
    >>> import time
    >>> microcache.upsert('has', 'gone', ttl=2)
    >>> microcache.has('has')
    True
    >>> time.sleep(2)
    >>> microcache.has('has')
    False
    """
    _set_log_level()
    logger.debug('has({})'.format(key))
    return options.enabled and key in _CACHE.keys() and not _CACHE[key].is_expired()


def upsert(key, value, ttl=None):
    """ Perform an upsert on the cache

    >>> import microcache
    >>> microcache.get('upsert')
    >>> microcache.upsert('upsert', 'this')
    >>> microcache.get('upsert')
    'this'
    >>> microcache.upsert('upsert', 'that', ttl=5)
    >>> microcache.get('upsert')
    'that'
    """
    _set_log_level()
    logger.debug('upsert({}, {})'.format(key, value))
    if not options.enabled:
        return
    _CACHE[key] = MicrocacheItem(value, ttl)


def get(key, default=None):
    """ Get a value out of the cache, return default if key not found
    or cache is disabled

    >>> import microcache
    >>> microcache.get('get')
    >>> microcache.get('get', 'default')
    'default'
    >>> microcache.upsert('get', 'got')
    >>> microcache.get('get', 'default')
    'got'
    """
    _set_log_level()
    logger.debug('get({}, default={})'.format(key, default))
    if has(key):
        return _CACHE[key].value
    return default


def clear(key=None):
    """ Clear a cache entry, or the entire cache if no key is given

    >>> import microcache
    >>> microcache.upsert('clear', 'now')
    >>> microcache.upsert("don't", 'yet')
    >>> microcache.has('clear')
    True
    >>> microcache.has("don't")
    True
    >>> microcache.clear('clear')
    >>> microcache.has('clear')
    False
    >>> microcache.has("don't")
    True
    >>> microcache.clear()
    >>> microcache.has("don't")
    False
    """
    _set_log_level()
    logger.debug('clear({})'.format(key))
    if key is not None and key in _CACHE.keys():
        del _CACHE[key]
    elif not key:
        for cached_key in [k for k in _CACHE.keys()]:
            del _CACHE[cached_key]


@decorator.decorator
def this(func, ttl=None, *args, **kwargs):
    """ Use the cache as a decorator, essentially this with an override

    >>> import microcache
    >>> @microcache.this(ttl=2)
    ... def dummy():
    ...     print('in the func')
    ...     return 'value'
    ...
    >>> import time
    >>> dummy()
    in the func
    'value'
    >>> dummy()
    'value'
    >>> time.sleep(2)
    >>> dummy()
    in the func
    'value'
    """
    _set_log_level()
    key = func.__name__ + str(args) + str(kwargs)
    logger.debug('this({})'.format(key))
    if has(key):
        return get(key)
    value = func(*args, **kwargs)
    if options.enabled:
        upsert(key, value, ttl)
    return value


def disable(clear_cache=True):
    """ Disable the cache and clear its contents

    >>> import microcache
    >>> microcache.upsert('disable', 'me')
    >>> microcache.disable()
    >>> microcache.has('disable')
    False
    >>> microcache.enable()
    >>> microcache.has('disable')
    False
    """
    if clear_cache:
        clear()
    options.enabled = False


def enable():
    """ (Re)enable the cache

    >>> import microcache
    >>> microcache.disable()
    >>> microcache.upsert('enable', 'or not')
    >>> microcache.has('enable')
    False
    >>> microcache.enable()
    >>> microcache.upsert('enable', 'now')
    >>> microcache.has('enable')
    True
    """
    options.enabled = True


@contextlib.contextmanager
def temporarily_disabled():
    """ Temporarily disable the cache (useful for testing)

    >>> import microcache
    >>> with microcache.temporarily_disabled():
    ...     microcache.upsert('temp', 'disable')
    ...
    >>> microcache.has('temp')
    False
    """
    old_setting = options.enabled
    options.enabled = False
    yield
    options.enabled = old_setting


@contextlib.contextmanager
def temporarily_enabled():
    """ Temporarily enable the cache (useful for testing)

    >>> import microcache
    >>> with microcache.temporarily_disabled():
    ...     with microcache.temporarily_enabled():
    ...         microcache.upsert('temp', 'disable')
    ...
    >>> microcache.has('temp')
    True
    """
    old_setting = options.enabled
    options.enabled = True
    yield
    options.enabled = old_setting
