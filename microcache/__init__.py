import logging
from contextlib import contextmanager
from ._version import __version__, __version_info__  # flake8: noqa

logger = logging.getLogger(__name__)
_CACHE = {}


class Options(object):
    def __init__(self):
        self.enabled = True


options = Options()


def has(key):
    """ See if a key is in the cache

    >>> import microcache
    >>> microcache.has('has')
    False
    >>> microcache.upsert('has', 'now')
    >>> microcache.has('has')
    True
    """
    logger.debug('has({})'.format(key))
    return key in _CACHE.keys() and options.enabled


def upsert(key, value):
    """ Perform an upsert on the cache

    >>> import microcache
    >>> microcache.get('upsert')
    >>> microcache.upsert('upsert', 'this')
    >>> microcache.get('upsert')
    'this'
    >>> microcache.upsert('upsert', 'that')
    >>> microcache.get('upsert')
    'that'
    """
    logger.debug('upsert({}, {})'.format(key, value))
    if not options.enabled:
        return
    _CACHE[key] = value


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
    logger.debug('get({}, default={})'.format(key, default))
    if has(key):
        return _CACHE[key]
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
    logger.debug('clear({})'.format(key))
    if not options.enabled:
        return
    elif key is not None and key in _CACHE.keys():
        del _CACHE[key]
    elif not key:
        for cached_key in [k for k in _CACHE.keys()]:
            del _CACHE[cached_key]


def this(func):
    """ Use the cache as a decorator, essentially this with an override

    >>> import microcache
    >>> @microcache.this
    ... def dummy():
    ...     print('in the func')
    ...     return 'value'
    ...
    >>> dummy()
    in the func
    'value'
    >>> dummy()
    'value'
    """

    def func_wrapper(*args, **kwargs):
        key = func.__name__ + str(args) + str(kwargs)
        logger.debug('this({})'.format(key))
        if has(key) and options.enabled:
            return get(key)
        value = func(*args, **kwargs)
        if options.enabled:
            upsert(key, value)
        return value

    return func_wrapper


def disable():
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


@contextmanager
def temporarily_disabled():
    """ Temporarily disable the cache (useful for testing)

    >>> import microcache
    >>> with microcache.temporarily_disabled():
    ...     microcache.upsert('temp', 'disable')
    ...
    >>> microcache.has('temp')
    False
    """
    options.enabled = False
    yield
    options.enabled = True
