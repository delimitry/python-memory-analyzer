# python-memory-analyzer
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](https://github.com/delimitry/python-memory-analyzer/blob/master/LICENSE)

A tool for finding specific objects in the CPython process

Description:
------------

[WIP]
A tool in pure CPython for finding specific objects (e.g. `str`, `int`, `float`, etc) in the CPython process


Usage example:
--------------
```
usage: python-memory-analyzer.py [-h] -p PID [-d] [-v]

Python memory analyzer

optional arguments:
  -h, --help         show this help message and exit
  -p PID, --pid PID  process ID (requires root privileges)
  -d, --debug        run in debug mode
  -v, --version      show program's version number and exit
```

```
$ sudo python python-memory-analyzer.py -p 32123
```

License:
--------
Released under [The MIT License](https://github.com/delimitry/python-memory-analyzer/blob/master/LICENSE).
