#!/usr/bin/env python
#-*- coding: utf8 -*-

from __future__ import print_function, unicode_literals

import struct
import unittest
from io import BytesIO
from objects import PyStringObject


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
        self.assertEqual(obj.ob_type, 0x8f9c60)
        self.assertEqual(obj.ob_size, 3)
        self.assertEqual(obj.ob_shash, 0x142a6050a178b2d7)
        self.assertEqual(obj.ob_sstate, 1)
        self.assertEqual(obj.ob_sval, b'asd')


if __name__ == '__main__':
    unittest.main(verbosity=2)
