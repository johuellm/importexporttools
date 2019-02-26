#!/usr/bin/python3
# -*- coding: utf-8 -*-
# author: Joschka Hüllmann <huellmann@uni-muenster.de>

import unittest

import os
import os.path
from glob import glob
import unicodecsv as csv
from io import BytesIO

import transform

class TestTransformMethods(unittest.TestCase):

  def test(self):
    self.assertEqual(1,1)

if __name__ == '__main__':
  unittest.main()
