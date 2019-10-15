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
    def get_size():
        return 1  # null character ('\x00')

    @staticmethod
    def format(value):
        return '{0} ({1})'.format(
            value.decode() if PY3 else value,
            value.hex() if PY3 else value.encode('hex')
        )


class _char_p_2(object):
    @staticmethod
    def read(stream):
        return read(stream, _char_p_2.length())

    @staticmethod
    def length():
        return ctypes.sizeof(ctypes.c_char_p)

    @staticmethod
    def format(value):
        return '{:016x}'.format(value)


class Py_hash_t(object):
    @staticmethod
    def read(stream):
        return read(stream, Py_ssize_t.get_size())

    @staticmethod
    def get_size():
        return ctypes.sizeof(ctypes.c_size_t)

    @staticmethod
    def format(value):
        return '{0} ({0:016x})'.format(value)


class state(object):
    def __init__(self, value=0):
        self.value = value
        first_byte = value & 0xff
        self.interned = first_byte & 0b11
        self.kind = (first_byte >> 2) & 0b111
        self.compact = (first_byte >> 5) & 0b1
        self.ascii = (first_byte >> 6) & 0b1
        self.ready = (first_byte >> 7) & 0b1

    @classmethod
    def read(cls, stream):
        value = read(stream, cls.get_size())
        if value > 0xff:
            raise Exception('Invalid state value')
        return cls(value)

    @staticmethod
    def get_size():
        return ctypes.sizeof(ctypes.c_size_t)

    @staticmethod
    def format(value):
        if isinstance(value, state):
            value = value.value
        first_byte = value & 0xff
        return '{:08b} (interned={} kind={} compact={} ascii={} ready={})'.format(
            first_byte,
            first_byte & 0b11,
            (first_byte >> 2) & 0b111,
            (first_byte >> 5) & 0b1,
            (first_byte >> 6) & 0b1,
            (first_byte >> 7) & 0b1
        )


class wchar_t_p(object):
    """Address of wstr"""
    @staticmethod
    def read(stream):
        return read(stream, wchar_t_p.get_size())

    @staticmethod
    def get_size():
        return ctypes.sizeof(ctypes.c_wchar_p)

    @staticmethod
    def format(value):
        return '{0} ({0:016x})'.format(value)


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
            result += field_type.get_size()
        return result

    def __repr__(self):
        return '\n'.join(
            '{} = {}'.format(field_name, field_type.format(getattr(self, field_name, None)))
            for field_type, field_name in self.fields
        )


###############################################################################
# CPython 3.7
###############################################################################

def is_ascii(value):
    return all(0x00 <= ord(x) <= 0x7f for x in value)


def is_compact_ascii(st):
    return st.kind == 1 and st.compact == 1 and st.ascii == 1 and st.ready == 1


def is_compact_not_ascii(st):
    return st.kind in [1, 2, 4] and st.compact == 1 and st.ascii == 0 and st.ready == 1


def is_legacy_string_not_ready(params):
    st = params['state']
    hv = params['hash']
    wstr = params['wstr']
    length = params['length']
    return st.kind == 0 and st.compact == 0 and st.ascii == 0 and st.ready == 0 and st.interned == 0 and \
        length == 0 and hv in [-1, (2 ** (8 * Py_hash_t.get_size())) - 1] and wstr == 0


def is_legacy_string_ready(st):
    return st.kind in [1, 2, 4] and st.compact == 0 and st.ascii in [0, 1] and st.ready == 1


class PyASCIIObject(object):
    """
    See: https://github.com/python/cpython/blob/3.7/Include/unicodeobject.h
    """
    fields = [
        (Py_ssize_t, 'ob_refcnt'),  # PyObject_HEAD
        (_typeobject_p, 'ob_type'),  # PyObject_HEAD
        (Py_ssize_t, 'length'),
        (Py_hash_t, 'hash'),
        (state, 'state'),
        (wchar_t_p, 'wstr'),
        # for PyASCIIObject the data immediately follow the structure
        (_char_p, 'data'),
    ]

    def __init__(self, **kwargs):
        for field in self.fields:
            field_type, field_name = field
            setattr(self, field_name, kwargs[field_name])

    @classmethod
    def get_size(cls):
        result = 0
        for field in cls.fields:
            field_type, _ = field
            result += field_type.get_size()
        return result

    def __repr__(self):
        return '\n'.join(
            '{} = {}'.format(field_name, field_type.format(getattr(self, field_name, None)))
            for field_type, field_name in self.fields
        )


class PyCompactUnicodeObject(object):
    fields = [
        (Py_ssize_t, 'ob_refcnt'),  # PyObject_HEAD
        (_typeobject_p, 'ob_type'),  # PyObject_HEAD
        (Py_ssize_t, 'length'),
        (Py_hash_t, 'hash'),
        (state, 'state'),
        (wchar_t_p, 'wstr'),
        # Non-ASCII strings
        (Py_ssize_t, 'utf8_length'),
        (_char_p_2, 'utf8'),  # TODO: check this
        (Py_ssize_t, 'wstr_length'),
        (_char_p, 'data'),
    ]

    def __init__(self, **kwargs):
        for field in self.fields:
            field_type, field_name = field
            setattr(self, field_name, kwargs[field_name])

    @classmethod
    def get_size(cls):
        result = 0
        for field in cls.fields:
            field_type, _ = field
            result += field_type.get_size()
        return result

    def __repr__(self):
        return '\n'.join(
            '{} = {}'.format(field_name, field_type.format(getattr(self, field_name, None)))
            for field_type, field_name in self.fields
        )


class PyUnicodeObject(object):
    fields = [
        (Py_ssize_t, 'ob_refcnt'),  # PyObject_HEAD
        (_typeobject_p, 'ob_type'),  # PyObject_HEAD
        (Py_ssize_t, 'length'),
        (Py_hash_t, 'hash'),
        (state, 'state'),
        (wchar_t_p, 'wstr'),
        (Py_ssize_t, 'utf8_length'),
        (_char_p_2, 'utf8'),  # TODO: check this
        (Py_ssize_t, 'wstr_length'),
        (_char_p, 'data'),
    ]

    def __init__(self, **kwargs):
        for field in self.fields:
            field_type, field_name = field
            setattr(self, field_name, kwargs[field_name])

    @classmethod
    def get_size(cls):
        result = 0
        for field in cls.fields:
            field_type, _ = field
            result += field_type.get_size()
        return result

    def __repr__(self):
        return '\n'.join(
            '{} = {}'.format(field_name, field_type.format(getattr(self, field_name, None)))
            for field_type, field_name in self.fields
        )


class PyCommonUnicodeObject(object):
    fields = [
        (Py_ssize_t, 'ob_refcnt'),  # PyObject_HEAD
        (_typeobject_p, 'ob_type'),  # PyObject_HEAD
        (Py_ssize_t, 'length'),
        (Py_hash_t, 'hash'),
        (state, 'state'),
        (wchar_t_p, 'wstr'),
    ]

    @classmethod
    def read(cls, stream):
        result = {}
        for field in cls.fields:
            field_type, field_name = field
            result[field_name] = field_type.read(stream)
        if is_compact_ascii(result['state']):
            data = _char_p.read(stream)
            assert len(data) == result['length'], 'Expected length != actual one'
            result['data'] = data.encode('utf-8')
            return PyASCIIObject(**result)
        else:
            compact_not_ascii = is_compact_not_ascii(result['state'])
            legacy_string_not_ready = is_legacy_string_not_ready(result)
            legacy_string_ready = is_legacy_string_ready(result['state'])
            if compact_not_ascii or legacy_string_not_ready or legacy_string_ready:
                utf8_length = Py_ssize_t.read(stream)
                result['utf8_length'] = utf8_length
                utf8 = _char_p_2.read(stream)  # TODO: check this
                result['utf8'] = utf8
                wstr_length = Py_ssize_t.read(stream)
                result['wstr_length'] = wstr_length
                # read data
                length = result['length']
                state = result['state']
                if state.kind == 1:
                    data = stream.read(length)
                    data = data.decode('utf-8')
                elif state.kind == 2:
                    data = stream.read(length * 2)
                    data = data.decode('utf-16le')
                elif state.kind == 4:
                    data = stream.read(length * 4)
                    data = data.decode('utf-32le')
                # data starts just after the structure
                result['data'] = data.encode('utf-8')
            if compact_not_ascii:
                return PyCompactUnicodeObject(**result)
            elif legacy_string_not_ready:
                return PyUnicodeObject(**result)
            elif legacy_string_ready:
                return PyUnicodeObject(**result)
