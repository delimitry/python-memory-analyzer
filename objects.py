# -*- coding: utf-8 -*-

from __future__ import print_function

import ctypes
import struct
import sys
from io import BytesIO


PY3 = sys.version_info[0] == 3


def read(stream, size):
    data = stream.read(size)
    types = {1: 'B', 2: 'H', 4: 'I', 8: 'Q'}
    return struct.unpack(types[size], data)[0]


###############################################################################
# C and CPython objects
###############################################################################

class Py_ssize_t(object):
    @staticmethod
    def read(stream):
        return read(stream, Py_ssize_t.get_size())

    @staticmethod
    def get_size():
        return ctypes.sizeof(ctypes.c_size_t)

    @staticmethod
    def format(value):
        return '{0} ({0:016x})'.format(value)

class _typeobject_p(object):
    """Address of _typeobject"""
    @staticmethod
    def read(stream):
        return read(stream, _typeobject_p.get_size())

    @staticmethod
    def get_size():
        return ctypes.sizeof(ctypes.c_void_p)

    @staticmethod
    def format(value):
        return '{0} ({0:016x})'.format(value)


class _long(object):
    @staticmethod
    def read(stream):
        return read(stream, _long.get_size())

    @staticmethod
    def get_size():
        return ctypes.sizeof(ctypes.c_long)

    @staticmethod
    def format(value):
        return '{0} ({0:016x})'.format(value)


class _int(object):
    @staticmethod
    def read(stream):
        return read(stream, _int.get_size())

    @staticmethod
    def get_size():
        return ctypes.sizeof(ctypes.c_int)

    @staticmethod
    def format(value):
        return '{0} ({0:08x})'.format(value)


class _char_p(object):
    @staticmethod
    def read(stream, length=None):
        if length:
            return stream.read(length)
        else:
            out = b''
            while True:
                offset = stream.tell()
                b = stream.read(1)
                if not b:
                    break
                if b == b'\x00':
                    stream.seek(offset)
                    break
                out += b
            return out

    @staticmethod
    def get_size(self):
        return 1  # null character ('\x00')

    @staticmethod
    def format(value):
        return '{0} ({1})'.format(value.decode(), value.hex() if PY3 else value.encode('hex'))


###############################################################################
# CPython 2.7
###############################################################################

class PyStringObject(object):
    """
    See: https://github.com/python/cpython/blob/2.7/Include/stringobject.h
    """
    fields = [
        (Py_ssize_t, 'ob_refcnt'),  # PyObject_VAR_HEAD / PyObject_HEAD
        (_typeobject_p, 'ob_type',),  # PyObject_VAR_HEAD / PyObject_HEAD
        (Py_ssize_t, 'ob_size'),  # PyObject_VAR_HEAD
        (_long, 'ob_shash'),
        (_int, 'ob_sstate'),
        (_char_p, 'ob_sval'),
    ]

    def __init__(self, **kwargs):
        for field in self.fields:
            field_type, field_name = field
            setattr(self, field_name, kwargs[field_name])

    @classmethod
    def read(cls, stream):
        result = {}
        for field in cls.fields:
            field_type, field_name = field
            result[field_name] = field_type.read(stream)
        return cls(**result)

    @classmethod
    def get_size(cls):
        result = 0
        for field in cls.fields:
            field_type, _ = field
            result += field_type().get_size()
        return result

    def __repr__(self):
        return '\n'.join(
            '{} = {}'.format(field_name, field_type.format(getattr(self, field_name, None)))
            for field_type, field_name in self.fields
        )
