# microcache

[![Latest Version](https://img.shields.io/pypi/v/microcache.svg)](https://pypi.python.org/pypi/microcache)
[![Build Status](https://travis-ci.org/ajk8/microcache.svg?branch=master)](https://travis-ci.org/ajk8/microcache)

A Really! Small! Cache! for python 2 and 3.

## Why?

Working on a totally separate project, I found myself wanting to use [funcy.memoize](http://funcy.readthedocs.org/en/stable/calc.html#memoize)...a lot.  There was a major problem, though: I couldn't test with it.  There was no (obvious) way to turn it off.  It was making me crazy, so I spent a few hours writing a small module (even smaller than this, originally) to suit the memoization needs, with a hook to turn it off for testing.  When I got to the end of my feature sprint for that project, I decided it made more sense to spin it out into its own project, so here we are!

## Current features

* Simple upsert and get workflow
* Decorator for "memoization"
* Enabling and disabling functionality, including a context manager
* Work directly on the imported module... no additional instantiation

## Installation

```
pip install microcache
```

## Examples

Basic usage
```python
>>> import microcache
>>> microcache.has('key')
False
>>> microcache.get('key', default='default')
'default'
>>> microcache.upsert('key', 'value')
>>> microcache.get('key')
'value'
>>> microcache.disable()
>>> microcache.get('key')
```

Decorator and context manager
```python
import microcache
import time

@microcache.this
def somefunc():
    time.sleep(5)
    return "this will be cached, and you won't have to wait a second time!"

def test_somefunc():
    somefunc()
    somefunc()
    with microcache.temporarily_disabled():
        # now we'll have to wait again
        somefunc()
```
