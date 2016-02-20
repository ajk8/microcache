from setuptools import setup, find_packages

with open('microcache/_version.py') as f:
    exec(f.read())

setup(
    name='microcache',
    version=__version__,
    description='Really! Small! Cache!',
    author='Adam Kaufman',
    author_email='kaufman.blue@gmail.com',
    url='https://github.com/ajk8/microcache',
    download_url='https://github.com/ajk8/microcache/tarball/' + __version__,
    license='MIT',
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development'
    ],
    keywords='virtualenv development'
)
