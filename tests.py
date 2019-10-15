#!/usr/bin/env python
#-*- coding: utf8 -*-

from __future__ import print_function, unicode_literals

import struct
import unittest
from io import BytesIO
from objects import PyStringObject, PyCommonUnicodeObject, PY3


class Test(unittest.TestCase):
    """
    Test python memory analyzer
    """

    def test_py_str_read_py27(self):
        mem_dump = BytesIO(
            b'\x01\x00\x00\x00\x00\x00\x00\x00`\x9c\x8f\x00\x00\x00\x00\x00'
            b'\x03\x00\x00\x00\x00\x00\x00\x00\xd7\xb2x\xa1P`*\x14'
            b'\x01\x00\x00\x00asd\x00'
        )
        obj = PyStringObject.read(mem_dump)
        self.assertEqual(obj.ob_refcnt, 1)
        self.assertEqual(obj.ob_type, 0x8f9c60)
        self.assertEqual(obj.ob_size, 3)
        self.assertEqual(obj.ob_shash, 0x142a6050a178b2d7)
        self.assertEqual(obj.ob_sstate, 1)
        self.assertEqual(obj.ob_sval.decode('utf-8'), 'asd')

    def test_py_unicode_read_py37(self):
        mem_dump = BytesIO(
            b'\x01\x00\x00\x00\x00\x00\x00\x00\xc0\x92\xa4\x00\x00\x00\x00\x00'
            b'\x03\x00\x00\x00\x00\x00\x00\x00\xc5\xf2\xda3\xc4\x1f\xff\xeb\xa8'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x000\x041\x042\x04\x00\x001\x042\x04\x00'
        )
        obj = PyCommonUnicodeObject.read(mem_dump)
        self.assertEqual(obj.ob_refcnt, 1)
        self.assertEqual(obj.ob_type, 0x0000000000a492c0)
        self.assertEqual(obj.length, 3)
        self.assertEqual(obj.hash, 0xebff1fc433daf2c5)
        self.assertEqual(obj.state.value, 0b10101000)
        self.assertEqual(obj.data.decode('utf-8'), 'абв')


if __name__ == '__main__':
    unittest.main(verbosity=2)
