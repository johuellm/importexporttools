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

  def test_add_to_mapping(self):
    mapping = {}
    testdata = {"source@test.de","Target <target@test.de>", "source@test.de","\"Target, Bot\" <target@test.de>","source@test.de","target@test.de", \
      "source@test.de","Multiple Target 1 <test@test.de>, Target 2 <test2@test.de>", "undisclosed-recipients:;"}
    transform.add_to_mapping(mapping, 1, testdata)
    self.assertEqual(set(mapping.keys()), {"source@test.de", "target@test.de", "test@test.de", "test2@test.de", "undisclosed-recipients"})
    self.assertEqual(set(mapping.values()), {1,2,3,4,5})


  def test_check_special_addresses(self):
    test_addresses1 = ["undisclosed-recipients:;", "undisclosed recipients:;", "verborgene_empfaenger: ;"]
    test_addresses2 = ["normal@address.de", ""]
    for test_addr in test_addresses1:
      addr,ret = transform.check_special_addresses(test_addr)
      self.assertEqual(addr, "undisclosed-recipients")
      self.assertTrue(ret)
    for test_addr in test_addresses2:
      addr,ret = transform.check_special_addresses(test_addr)
      self.assertEqual(addr, test_addr)
      self.assertFalse(ret)

  def test_integration(self):
    testcsv = ''' "Comunio.de Aktivitaetserinnerung","mailbot@comunio.de","user@web.de",31.12.2014 04:57, 
"Test Good news, Here YouCan Get ExclusiveTablet  :-)","Darrell <du@prosegarden.net>","user@web.de",04.01.2015 23:07, 
"Re: Ihre Angebotsanfrage","""Finn Schmitz"" <fsiwd@calgaryartistssociety.com>","angela.aust@web.de",06.01.2015 00:40, 
"Ihr Traumpartner wartet auf Sie - PARSHIP 20 günstiger! +++ WEB.DE Gutscheinportal mit Geschenk!","""WEB.DE Vorteilswelt"" <neu@web.de>","user@web.de",06.01.2015 06:53, 
"Test OrderMeds ;-)","Mitchell <eftaldd@amega.com>","""user@web.de"" <user@web.de>",06.01.2015 19:28, 
"Attention Test To a dilemma which appeared inane","Support Service <dtamiezu@flipag.net>","""user@web.de"" <user@web.de>",07.01.2015 09:06, 
"LinkedInReminder has sent you a personal message","LinkedInReminder <gluecken1978@dhascpa.com>","""user@web.de"" <user@web.de>",07.01.2015 10:09, 
"Ihre Buchung wurde storniert! KFI28384773-2014","""Luisa Ludwig"" <rlksdu@haukelihytter.no>","k.g.hahn@web.de",07.01.2015 16:28, 
"Buchung vom 17.10.14 best�tigt","""Mara Walter"" <jwxixj@mbacrystalball.com>","robert.rau@web.de",08.01.2015 13:16, 
"Kostenlos im Internet und unterwegs fernsehen mit Zattoo HiQ","""WEB.DE informiert"" <neu@web.de>","user@web.de",08.01.2015 17:51, 
"blablabla","""Mann, User"" <user@web.de>","User1 <user1@web.de>, User2 <user2@web.de>, ""Bot, User"" <user3@web.de>",01.01.2005 12:22, 
"blablabla","""Mann, User"" <user@web.de>","=?UTF-8?Q?Marcel_H=C3=BCkker?= <user@web.de>",01.01.2005 12:22, 
'''

    expectedcsvs = b'''1,1,2,31.12.2014 04:57
2,3,2,04.01.2015 23:07
3,4,5,06.01.2015 00:40
4,6,2,06.01.2015 06:53
5,7,2,06.01.2015 19:28
6,8,2,07.01.2015 09:06
7,9,2,07.01.2015 10:09
8,10,11,07.01.2015 16:28
9,12,13,08.01.2015 13:16
10,6,2,08.01.2015 17:51
11,2,14,01.01.2005 12:22
11,2,15,01.01.2005 12:22
11,2,16,01.01.2005 12:22
12,2,2,01.01.2005 12:22
'''

    expectedmappingcsvs = b'''mailbot@comunio.de,1
user@web.de,2
du@prosegarden.net,3
fsiwd@calgaryartistssociety.com,4
angela.aust@web.de,5
neu@web.de,6
eftaldd@amega.com,7
dtamiezu@flipag.net,8
gluecken1978@dhascpa.com,9
rlksdu@haukelihytter.no,10
k.g.hahn@web.de,11
jwxixj@mbacrystalball.com,12
robert.rau@web.de,13
user1@web.de,14
user2@web.de,15
user3@web.de,16
'''

    try:
      with open("transform_test.csv.temp","w") as fp:
        fp.write(testcsv)

      index = 1
      mapping = {}
      files = glob("transform_test.csv.temp")
      for file in files:
        index = transform.add_to_mapping(mapping, index, transform.parse_csv_to_unique_addresses(file))
      print("mapped %d (%d) addresses." % (len(mapping), index-1))

      if not os.path.isdir("anon"):
        os.makedirs("anon")

      for file in files:
        transform.process(mapping, file)
      print("processed %d files." % len(files))

      with open(os.path.join("anon", "mapping.csv"), 'wb') as wp:
          writer = csv.writer(wp, delimiter=',', quotechar='"')
          for kv in mapping.items():
            writer.writerow(kv)
      print("saved mapping as %s" % os.path.join("anon", "mapping.csv"))

      self.assertEqual(set(mapping.keys()), {"mailbot@comunio.de","user@web.de", "du@prosegarden.net", "fsiwd@calgaryartistssociety.com", "angela.aust@web.de", "neu@web.de", \
        "eftaldd@amega.com", "dtamiezu@flipag.net", "gluecken1978@dhascpa.com", "rlksdu@haukelihytter.no", "k.g.hahn@web.de", "jwxixj@mbacrystalball.com", "robert.rau@web.de", \
        "user1@web.de", "user2@web.de", "user3@web.de"})

      with open(os.path.join("anon","transform_test.csv.temp.anon.csv"), "rb") as fp:
        targetcsv = []
        reader = csv.reader(fp, delimiter=',', quotechar='"')
        for row in reader:
          targetcsv.append(row)

      expectedcsv = []
      fcsv = BytesIO(expectedcsvs)
      reader = csv.reader(fcsv, delimiter=',', quotechar='"')
      for row in reader:
        expectedcsv.append(row)

      
      # compare columnwise
      self.assertCountEqual([x[0] for x in targetcsv], [x[0] for x in expectedcsv])
      # must compare together as order and counts differs across both columns
      self.assertEqual(set([x[1] for x in targetcsv])|set([x[2] for x in targetcsv]), set([x[1] for x in expectedcsv])|set([x[2] for x in expectedcsv]))
      self.assertCountEqual([x[3] for x in targetcsv], [x[3] for x in expectedcsv])

      with open(os.path.join("anon","mapping.csv"), "rb") as fp:
        targetmappingcsv = []
        reader = csv.reader(fp, delimiter=',', quotechar='"')
        for row in reader:
          targetmappingcsv.append(row)

      expectedmappingcsv = []
      fcsv = BytesIO(expectedmappingcsvs)
      reader = csv.reader(fcsv, delimiter=',', quotechar='"')
      for row in reader:
        expectedmappingcsv.append(row)

      self.assertCountEqual([x[0] for x in targetmappingcsv], [x[0] for x in expectedmappingcsv])
      self.assertCountEqual([x[1] for x in targetmappingcsv], [x[1] for x in expectedmappingcsv])

    finally:
      if os.path.exists("transform_test.csv.temp"):
        os.remove("transform_test.csv.temp")

      if os.path.exists(os.path.join("anon","transform_test.csv.temp.anon.csv")):
        os.remove(os.path.join("anon", "transform_test.csv.temp.anon.csv"))

      if os.path.exists(os.path.join("anon","mapping.csv")):
        os.remove(os.path.join("anon", "mapping.csv"))

      if os.path.isdir("anon"):
        os.rmdir("anon")

if __name__ == '__main__':
  unittest.main()
