import microcache


def test_has_disabled():
    microcache.upsert('test_has_disabled', 'value')
    assert microcache.has('test_has_disabled') is True
    microcache.options.enabled = False
    assert microcache.has('test_has_disabled') is False
    microcache.options.enabled = True


def test_upsert_disabled():
    microcache.options.enabled = False
    microcache.upsert('test_upsert_disabled', 'value')
    assert microcache.has('test_upsert_disabled') is False
    microcache.options.enabled = True
    microcache.upsert('test_upsert_disabled', 'value')
    assert microcache.has('test_upsert_disabled') is True


def test_get_disabled():
    microcache.upsert('test_get_disabled', 'value')
    assert microcache.get('test_get_disabled') == 'value'
    microcache.options.enabled = False
    assert microcache.get('test_get_disabled') is None
    microcache.options.enabled = True


def test_clear_disabled():
    microcache.upsert('test_clear_disabled', 'value')
    microcache.options.enabled = False
    microcache.clear()
    microcache.options.enabled = True
    assert microcache.has('test_clear_disabled') is True


def test_this():

    entry = {'flag': False}

    @microcache.this
    def testable(arg, kwarg=None):
        entry['flag'] = True
        return arg, kwarg

    assert testable('arg') == ('arg', None)
    assert entry['flag'] is True
    entry['flag'] = False
    assert testable('arg') == ('arg', None)
    assert entry['flag'] is False
    assert testable('arg', 'kwarg') == ('arg', 'kwarg')
    assert entry['flag'] is True
    microcache.options.enabled = False
    entry['flag'] = False
    assert testable('arg') == ('arg', None)
    assert entry['flag'] is True
    microcache.options.enabled = True

