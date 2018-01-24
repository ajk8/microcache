from setuptools import setup
from imp import find_module, load_module

PROJECT_NAME = 'microcache'
GITHUB_USER = 'ajk8'
GITHUB_ROOT = 'https://github.com/{}/{}'.format(GITHUB_USER, PROJECT_NAME)

# pull in __version__ variable
found = find_module('_version', [PROJECT_NAME])
_version = load_module('_version', *found)

setup(
    name=PROJECT_NAME,
    version=_version.__version__,
    description='Really! Small! Cache!',
    author='Adam Kaufman',
    author_email='kaufman.blue@gmail.com',
    url=GITHUB_ROOT,
    download_url='{0}/tarball/{1}'.format(GITHUB_ROOT, _version.__version__),
    license='MIT',
    packages=[PROJECT_NAME],
    install_requires=[
        'decorator==4.2.1'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords='cache microcache memoize development'
)
