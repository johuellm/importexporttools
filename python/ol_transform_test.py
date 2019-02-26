#!/usr/bin/python3
# -*- coding: utf-8 -*-
# author: Joschka Hüllmann <huellmann@uni-muenster.de>

import unittest

import os
import os.path
from glob import glob
import unicodecsv as csv
from io import BytesIO

import ol_transform

class TestTransformMethods(unittest.TestCase):

  def test_get_format_date(self):
    
    goodDates = [
      ("Feb 26, 2019 14:15:16.001200329 UTC", "26.02.2019 14:15"),
      ("Mar 22, 2019 2:35:6.992200329 GMT", "22.03.2019 02:35"),
      ("Oct 22, 2019 2:35:6.992200329 GMT", "22.10.2019 02:35")
    ]

    badDates = [
      "Okt 22, 2019 2:35:6.992200329 CET",
      "Okt 22, 2019 2:35:6.992200329 CEST",
      "Okt 22, 2019 2:35:6.992200 UTC",
      "Jan 32, 2019 2:35:6.992200 UTC",
      "",
    ]

    for d_src,d_dst in goodDates:
      self.assertEqual(ol_transform.get_format_date(d_src),d_dst)

    for d in badDates:
      self.assertRaises(ValueError, ol_transform.get_format_date, d)

    self.assertRaises(TypeError, ol_transform.get_format_date, None)

  def test_get_recipients_str(self):
    recipients1 = ([("Alice", "EX"), ("Bob", "EX"), ("Charlie", "EX")], "Alice,Bob,Charlie")
    recipients2 = ([("Alice <alice@web.de>", "SMTP"), ("Bob <bob@gmail.come", "SMTP"), ("Charlie <charlie@charles.com>", "SMTP")], "Alice <alice@web.de>,Bob <bob@gmail.come,Charlie <charlie@charles.com>")
    recipients3 = ([],"")
    recipients4 = ([("Alice", "EX"),], "Alice")
    recipients5 = ["Alice",]
    recipients6 = [("Alice","EX","Third"),]
    recipients7 = "Alice"
    recipients8 = None

    self.assertEqual(ol_transform.get_recipients_str(recipients1[0]),recipients1[1])
    self.assertEqual(ol_transform.get_recipients_str(recipients2[0]),recipients2[1])
    self.assertEqual(ol_transform.get_recipients_str(recipients3[0]),recipients3[1])
    self.assertEqual(ol_transform.get_recipients_str(recipients4[0]),recipients4[1])
    
    self.assertRaises(TypeError, ol_transform.get_recipients_str, recipients5)
    self.assertRaises(TypeError, ol_transform.get_recipients_str, recipients6)
    self.assertRaises(TypeError, ol_transform.get_recipients_str, recipients7)
    self.assertRaises(TypeError, ol_transform.get_recipients_str, recipients8)

def test_integration(self):
    self.fail("Not implemented yet.")

if __name__ == '__main__':
  unittest.main()
