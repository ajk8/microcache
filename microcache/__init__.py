import contextlib
import decorator
import logging
import sys
import time
from ._version import __version__, __version_info__  # flake8: noqa

logger = logging.getLogger('microcache')
logger.addHandler(logging.NullHandler())


class MicrocacheOptions(object):
    """
    Global functioning options for the cache:

        enabled: setting that is checked before any upsert or fetch operations
        debug: setting that manages logging level (use in concert with init_logging())
    """

    def __init__(self):
        self._enabled = True
        self._debug = False
        logger.setLevel(logging.INFO)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if not isinstance(value, bool):
            raise TypeError('MicrocacheOptions.enabled must be a bool')
        self._enabled = value

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        if not isinstance(value, bool):
            raise TypeError('MicrocacheOptions.debug must be a bool')
        self._debug = value
        logger.setLevel(logging.DEBUG if value else logging.INFO)


options = MicrocacheOptions()


def init_logging(stream=sys.stderr, filepath=None,
                 format='%(asctime).19s [%(levelname)s] %(name)s: %(message)s'):
    """
    Setup logging for the microcache module, but only do it once!

    :param stream: stream to log to (defaults to sys.stderr)
    :param filepath: path to a file to log to as well (defaults to None)
    :param format: override the default format with whatever you like
    """
    if not (len(logger.handlers) == 1 and isinstance(logger.handlers[0], logging.NullHandler)):
        logger.warn('logging has already been initialized, refusing to do it again')
        return
    formatter = logging.Formatter(format)
    if stream is not None:
        handler = logging.StreamHandler(stream=stream)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    if filepath is not None:
        handler = logging.FileHandler(filename=filepath)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.info('successfully initialized logger')


class MicrocacheItem(object):
    """
    Representation for an actual cache item which supports ttl
    """

    def __init__(self, value, ttl):
        self.value = value
        self.ttl = ttl
        self.timestamp = time.time()

    def is_expired(self):
        if self.ttl is None:
            return False
        ret = time.time() - self.timestamp > self.ttl
        if ret:
            logger.debug('cached item expired after {} seconds'.format(self.ttl))
        return ret


class NotObject(object):
    """
    Object that always fails the truthiness test
    """

    def __init__(self, repr_str):
        self.repr_str = repr_str

    def __bool__(self):
        # for python 3 compatibility
        return False

    def __nonzero__(self):
        # for python 2 compatibility
        return False

    def __repr__(self):
        return self.repr_str


# special objects that denote "error codes", differentiating from None
CACHE_MISS = NotObject('CACHE_MISS')
CACHE_DISABLED = NotObject('CACHE_DISABLED')


class Microcache(object):
    """
    Really! Small! Cache!
    """

    def __init__(self, options_obj):
        self._dict = {}
        self.options = options_obj

    def has(self, key):
        """
        See if a key is in the cache

        Returns CACHE_DISABLED if the cache is disabled

        :param key: key to search for
        """
        if not self.options.enabled:
            return CACHE_DISABLED
        ret = key in self._dict.keys() and not self._dict[key].is_expired()
        logger.debug('has({}) == {}'.format(repr(key), ret))
        return ret

    def upsert(self, key, value, ttl=None):
        """
        Perform an upsert on the cache

        Returns CACHE_DISABLED if the cache is disabled
        Returns True on successful operation

        :param key: key to store the value under
        :param value: value to cache
        :param ttl: optional expiry in seconds (defaults to None)
        """
        if not self.options.enabled:
            return CACHE_DISABLED
        logger.debug('upsert({}, {}, ttl={})'.format(repr(key), repr(value), ttl))
        self._dict[key] = MicrocacheItem(value, ttl)
        return True

    def get(self, key, default=CACHE_MISS):
        """
        Get a value out of the cache

        Returns CACHE_DISABLED if the cache is disabled

        :param key: key to search for
        :param default: value to return if the key is not found (defaults to CACHE_MISS)
        """
        if not self.options.enabled:
            return CACHE_DISABLED
        ret = default
        if self.has(key):
            ret = self._dict[key].value
        logger.debug('get({}, default={}) == {}'.format(repr(key), repr(default), repr(ret)))
        return ret

    def clear(self, key=None):
        """
        Clear a cache entry, or the entire cache if no key is given

        Returns CACHE_DISABLED if the cache is disabled
        Returns True on successful operation

        :param key: optional key to limit the clear operation to (defaults to None)
        """
        if not self.options.enabled:
            return CACHE_DISABLED
        logger.debug('clear(key={})'.format(repr(key)))
        if key is not None and key in self._dict.keys():
            del self._dict[key]
            logger.info('cache cleared for key: ' + repr(key))
        elif not key:
            for cached_key in [k for k in self._dict.keys()]:
                del self._dict[cached_key]
            logger.info('cache cleared for ALL keys')
        return True

    def disable(self, clear_cache=True):
        """
        Disable the cache and clear its contents

        :param clear_cache: clear the cache contents as well as disabling (defaults to True)
        """
        logger.debug('disable(clear_cache={})'.format(clear_cache))
        if clear_cache:
            self.clear()
        self.options.enabled = False
        logger.info('cache disabled')

    def enable(self):
        """
        (Re)enable the cache
        """
        logger.debug('enable()')
        self.options.enabled = True
        logger.info('cache enabled')

    @contextlib.contextmanager
    def temporarily_disabled(self):
        """
        Temporarily disable the cache (useful for testing)
        """
        old_setting = self.options.enabled
        self.disable(clear_cache=False)
        try:
            yield
        finally:
            self.options.enabled = old_setting

    @contextlib.contextmanager
    def temporarily_enabled(self):
        """
        Temporarily enable the cache (useful for testing)
        """
        old_setting = self.options.enabled
        self.enable()
        try:
            yield
        finally:
            self.options.enabled = old_setting


CACHE_OBJ = Microcache(options_obj=options)


def has(key):
    """
    See if a key is in the global cache

    Returns CACHE_DISABLED if the cache is disabled

    :param key: key to check for
    """
    return CACHE_OBJ.has(key)


def upsert(key, value, ttl=None):
    """
    Perform an upsert on the global cache

    Returns CACHE_DISABLED if the cache is disabled

    :param key: key to store the value under
    :param value: value to cache
    :param ttl: optional expiry in seconds (defaults to None)
    """
    return CACHE_OBJ.upsert(key, value, ttl)


def get(key, default=CACHE_DISABLED):
    """
    Get a value out of the global cache

    Returns CACHE_DISABLED if the cache is disabled

    :param key: key to search for
    :param default: value to return if the key is not found (defaults to CACHE_MISS)
    """
    return CACHE_OBJ.get(key, default)


def clear(key=None):
    """
    Clear an entry from the global cache, or the entire cache if no key is given

    Returns CACHE_DISABLED if the cache is disabled

    :param key: optional key to limit the clear operation to (defaults to None)
    """
    return CACHE_OBJ.clear(key)


def disable(clear_cache=True):
    """
    Disable the global cache and clear its contents

    :param clear_cache: clear the cache contents as well as disabling (defaults to True)
    """
    return CACHE_OBJ.disable(clear_cache)


def enable():
    """
    (Re)enable the cache
    """
    return CACHE_OBJ.enable()


@contextlib.contextmanager
def temporarily_disabled():
    """
    Temporarily disable the cache (useful for testing)
    """
    with CACHE_OBJ.temporarily_disabled():
        yield


@contextlib.contextmanager
def temporarily_enabled():
    """
    Temporarily enable the cache (useful for testing)
    """
    with CACHE_OBJ.temporarily_enabled():
        yield


@decorator.decorator
def this(func, cache_obj=CACHE_OBJ, key=None, ttl=None, *args, **kwargs):
    """
    Store the output from the decorated function in the cache and pull it
    from the cache on future invocations without rerunning.

    Normally, the value will be stored under a key which takes into account
    all of the parameters that are passed into it, thereby caching different
    invocations separately. If you specify a key, all invocations will be
    cached under that key, and different invocations will return the same
    value, which may be unexpected. So, be careful!

    If the cache is disabled, the decorated function will just run normally.

    Unlike the other functions in this module, you must pass a custom cache_obj
    to this() in order to operate on the non-global cache. This is because of
    wonky behavior when using decorator.decorator from a class method.

    :param func: (expensive?) function to decorate
    :param cache_obj: cache to a specific object (for use from the cache object itself)
    :param key: optional key to store the value under
    :param ttl: optional expiry to apply to the cached value
    :param *args: arg tuple to pass to the decorated function
    :param **kwargs: kwarg dict to pass to the decorated function
    """
    key = key or (func.__name__ + str(args) + str(kwargs))
    if cache_obj.has(key):
        return cache_obj.get(key)
    value = func(*args, **kwargs)
    cache_obj.upsert(key, value, ttl)
    return value
