import logging
import microcache
import os
import pytest
import sys
import time


def spoof_logger(monkeypatch, logger_name):
    monkeypatch.setattr(microcache, 'logger', logging.getLogger(logger_name))
    microcache.logger.addHandler(logging.NullHandler())
    microcache.logger.setLevel(logging.INFO)


def test_MicrocacheOptions(monkeypatch):
    spoof_logger(monkeypatch, 'test_MicrocacheOptions')
    options = microcache.MicrocacheOptions()
    assert options._enabled is True
    assert options._debug is False
    assert microcache.logger.level == logging.INFO
    with pytest.raises(TypeError):
        options.enabled = 'foo'
    options.enabled = False
    assert options.enabled is False
    with pytest.raises(TypeError):
        options.debug = None
    options.debug = True
    assert options.debug is True
    assert microcache.logger.level == logging.DEBUG


def test_init_logging(monkeypatch, capsys, tmpdir):
    spoof_logger(monkeypatch, 'test_init_logging')

    # no logger
    microcache.clear()
    out, err = capsys.readouterr()
    assert 'cache cleared' not in err
    assert 'clear(key=None)' not in err

    # first init
    microcache.init_logging(stream=sys.stderr)  # pass stderr explicitly so that capsys works
    out, err = capsys.readouterr()
    assert 'successfully initialized' in err
    assert 'already been initialized' not in err

    # second init
    microcache.init_logging()
    out, err = capsys.readouterr()
    assert 'successfully initialized' not in err
    assert 'already been initialized' in err

    # functioning logger
    microcache.clear()
    out, err = capsys.readouterr()
    assert 'cache cleared' in err
    assert 'clear(key=None)' not in err

    # debug logger
    microcache.options.debug = True
    microcache.clear()
    out, err = capsys.readouterr()
    assert 'cache cleared' in err
    assert 'clear(key=None)' in err

    # back to info logger
    microcache.options.debug = False
    microcache.clear()
    out, err = capsys.readouterr()
    assert 'cache cleared' in err
    assert 'clear(key=None)' not in err

    # file logger
    spoof_logger(monkeypatch, 'test_init_logging_with_file')
    with tmpdir.as_cwd():
        microcache.init_logging(stream=sys.stderr, filepath='file.log')
        microcache.clear()
        assert os.path.isfile('file.log')
        with open('file.log') as logfile:
            assert 'cache cleared' in logfile.read()


def test_MicrocacheItem():
    item = microcache.MicrocacheItem('foo', ttl=1)
    assert item.is_expired() is False
    time.sleep(1)
    assert item.is_expired() is True


def test_NotObject():
    notobject = microcache.NotObject('foo')
    assert not notobject and repr(notobject) == 'foo'
    assert not microcache.CACHE_DISABLED and repr(microcache.CACHE_DISABLED) == 'CACHE_DISABLED'
    assert not microcache.CACHE_MISS and repr(microcache.CACHE_MISS) == 'CACHE_MISS'


def test_Microcache_has_upsert():
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)
    assert cache.has('foo') is False
    assert cache.upsert('foo', 'bar') is True
    assert cache.has('foo') is True


def test_Microcache_get_upsert():
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)
    assert cache.upsert('foo', 'baz', ttl=1) is True
    assert cache.get('foo') == 'baz'
    time.sleep(1)
    assert cache.get('foo') is microcache.CACHE_MISS


def test_Microcache_clear_specific():
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)
    assert cache.upsert('foo', 'bar') is True
    assert cache.has('foo') is True
    assert cache.clear('foo') is True
    assert cache.has('foo') is False


def test_Microcache_clear_all():
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)
    assert cache.upsert('foo', 'bar') is True
    assert cache.upsert('unfoo', 'unbar') is True
    assert cache.clear() is True
    assert cache.has('foo') is False
    assert cache.has('unfoo') is False


def test_Microcache_disable_enable_with_clear():
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)
    assert cache.upsert('foo', 'bar') is True
    cache.disable()
    assert cache.has('foo') is microcache.CACHE_DISABLED
    assert cache.get('foo') is microcache.CACHE_DISABLED
    assert cache.clear() is microcache.CACHE_DISABLED
    cache.enable()
    assert cache.has('foo') is False  # the cache was cleared as part of disable()


def test_Microcache_disable_enable_without_clear():
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)
    assert cache.upsert('foo', 'bar') is True
    cache.disable(clear_cache=False)
    assert cache.has('foo') is microcache.CACHE_DISABLED
    cache.enable()
    assert cache.has('foo') is True


def test_Microcache_temporary_enable_disable():
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)
    assert cache.upsert('foo', 'bar') is True
    with cache.temporarily_disabled():
        assert cache.has('foo') is microcache.CACHE_DISABLED
        with cache.temporarily_enabled():
            assert cache.has('foo') is True
        assert cache.has('foo') is microcache.CACHE_DISABLED
    assert cache.has('foo') is True


def test_this_defaults(capsys):
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)

    @microcache.this(cache_obj=cache)
    def foo(bar='bar'):
        print('setting bar to: ' + bar)
        return bar

    assert foo() == 'bar'
    out, err = capsys.readouterr()
    assert out.strip() == 'setting bar to: bar'

    assert foo() == 'bar'
    out, err = capsys.readouterr()
    assert out.strip() == ''

    assert foo(bar='baz') == 'baz'
    out, err = capsys.readouterr()
    assert out.strip() == 'setting bar to: baz'

    assert foo() == 'bar'
    out, err = capsys.readouterr()
    assert out.strip() == ''

    assert foo(bar='baz') == 'baz'
    out, err = capsys.readouterr()
    assert out.strip() == ''


def test_this_custom_key(capsys):
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)

    @microcache.this(cache_obj=cache, key='foo')
    def foo(bar='bar'):
        print('setting bar to: ' + bar)
        return bar

    assert foo() == 'bar'
    out, err = capsys.readouterr()
    assert out.strip() == 'setting bar to: bar'
    assert cache.has('foo') is True

    assert foo(bar='baz') == 'bar'
    out, err = capsys.readouterr()
    assert out.strip() == ''
    assert cache.get('foo') == 'bar'


def test_this_ttl(capsys):
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)

    @microcache.this(cache_obj=cache, ttl=1)
    def foo(bar='bar'):
        print('setting bar to: ' + bar)
        return bar

    assert foo() == 'bar'
    out, err = capsys.readouterr()
    assert out.strip() == 'setting bar to: bar'

    assert foo() == 'bar'
    out, err = capsys.readouterr()
    assert out.strip() == ''

    time.sleep(1)

    assert foo() == 'bar'
    out, err = capsys.readouterr()
    assert out.strip() == 'setting bar to: bar'


def test_globals():

    @microcache.this
    def foo(bar='bar'):
        print('setting bar to: ' + bar)
        return bar

    assert foo() == 'bar'
    assert microcache.upsert('foo', 'bar') is True
    assert microcache.get('foo') == 'bar'
    assert microcache.has('baz') is False
    assert microcache.clear() is True
    microcache.disable()
    assert microcache.has('foo') is microcache.CACHE_DISABLED
    microcache.enable()
    with microcache.temporarily_disabled():
        assert microcache.upsert('foo', 'bar') is microcache.CACHE_DISABLED
        with microcache.temporarily_enabled():
            assert microcache.upsert('foo', 'baz') is True
        assert microcache.upsert('foo', 'bar') is microcache.CACHE_DISABLED
    assert microcache.get('foo') == 'baz'


def test_Microcache_get_items():
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)
    assert cache.upsert('unfoo', 'unbar') is True
    assert cache.upsert('foo', 'bar') is True
    assert cache.items() == [('foo', 'bar'), ('unfoo', 'unbar')]


def test_Microcache_get_items_with_filter():
    options = microcache.MicrocacheOptions()
    cache = microcache.Microcache(options_obj=options)
    assert cache.upsert('unfoo', 'unbar') is True
    assert cache.upsert('foo', 'bar') is True
    assert cache.upsert('foo/qux', 'baz') is True
    assert cache.items(path_root='foo') == [('foo', 'bar'), ('foo/qux', 'baz')]
