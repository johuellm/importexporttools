#!/usr/bin/python3
# -*- coding: utf-8 -*-
# author: Joschka Hüllmann <huellmann@uni-muenster.de>

""" transform.py: This module reads a .csv file produced by the Thunderbird addon importexporttools
                  and anonymizes its contents. The anonymised ids are constant across different
                  entries, when the same email occurs. A mapping.csv is created that shows the
                  mappings from email to anonymous id. The times and date of emails are preserved.

                  The structure of the csv files to be anonymized is given as (without headers):
                  SUBJECT,SOURCE,TARGET,TIME
"""

import sys
import email
import email.header
import email.utils
import os.path
import re
from glob import glob
import unicodecsv as csv

# Schema
SUBJECT = 0
SOURCE = 1
TARGET = 2
TIME = 3

# Does some address reach the maximum?
MAX_ADDRESS = 9999


def add_to_mapping(mapping, index, addresses):
  """ Adds a list of addresses to the mapping.

      Args:
        mapping: The existing mapping to add to.
        index: The current index, i.e. the anonymous id that is incremented.
        addresses: The list of adresses to process.
      Return:
        The updated index. """
  for addr in addresses:
    s_addr = split_address(addr)
    for s_a in s_addr:
      if s_a not in mapping:
        # sanity check with original address, adding normalized
        if len(addr) == MAX_ADDRESS:
          raise ValueError("Maximum address length reached: %s" % addr)
        mapping[s_a] = index
        index = index + 1
  return index


def parse_csv_to_unique_addresses(file):
  """ Parses a csv file to a set of addresses. 

      Args:
        file: The filename of the csv file. Delimiter is comma and
              quotechar is doublequote. Schema of the CSV file given
              at the top of this file .
      Return:
        The set of addresses. """
  addresses = []
  with open(file, 'rb') as fp:
    reader = csv.reader(fp, delimiter=',', quotechar='"')
    for row in reader:
      addresses.append(row[SOURCE])
      addresses.append(row[TARGET])
  return set(addresses)


def process(mapping, file):
  """ This function reads the input csv file and anonymizes it using the passed mapping.

      Args:
        mapping: The mapping to use. It is a hashmap with key being source email and value
                 being the anonymized id.
        file: The csv file to anonymize. Structure is given at the top of this file.
      Return:
        Nothing. """
  with open(file, 'rb') as fp:
    with open(os.path.join("anon", file + ".anon.csv"), 'wb') as wp:
      reader = csv.reader(fp, delimiter=',', quotechar='"')
      writer = csv.writer(wp, delimiter=',', quotechar='"')
      rowid = 0
      for row in reader:
        rowid = rowid + 1
        for s_addr_source in split_address(row[1]):
          s_addr_targets = split_address(row[2])
          # write a row with empty recipients if there are no recipients
          if len(s_addr_targets) > 0:
            for s_addr_target in s_addr_targets:
              writer.writerow([rowid, mapping[s_addr_source], mapping[s_addr_target], row[3]])
          else:
            writer.writerow([rowid, mapping[s_addr_source], "", row[3]])


def repair_address(addr):
  """ Removes leading and trailing quotes and doublequotes. Also removes some
      well known invalid email addresses and replaces it with "invalid-address".
      
      Args:
        addr: The given address to repair.
      Return:
        The repaired address. """
  # Some email addresses have two extra apostrophes
  if addr.startswith("'") and addr.endswith("'"): return addr[1:-1]
  if addr.startswith('"') and addr.endswith('"'): return addr[1:-1]
  # remove known invalid addresses
  if addr in ('"xxx\\""@xxx.de',): return "invalid-address"
  # else
  return addr


def check_special_addresses(addr):
  """ Similar to `repair_address(addr)`, but it is called at a different time in the process.
      Known addresses are reduced to a common denominator. Currently, only undisclosed recipients
      is considered.
      
      Args:
        addr: The address to check and potentially repair.
      Return:
        Returns a 2-tuple. First parameter is the repaired address and second parameter is true
        if anything was changed in the address, otherwise false. """
  # shortcut for undisclosed recipients
  addr = addr.lower().strip()
  if addr in ("undisclosed-recipients:;", "undisclosed recipients:;", "verborgene_empfaenger: ;"):
    return ("undisclosed-recipients", True)
  # else
  return (addr, False)


def split_address(addr):
  """ Takes a address value from the original input csv file and splits it into a set of
      single addresses, because each cell in the source csv file can contain multiple
      addresses according to the email headers specification.
      
      Args:
        addr: The address cell to split into single addresses.

      Return:
        A set of single addresses. """
  # shortcut for special addresses
  (addr, ret) = check_special_addresses(addr)
  if ret:
    return {addr,}

  addresses = []
  for to in email.utils.getaddresses([addr,]):
    # first split the email addresses
    # then decode using the provided encoding, or the default one (maybe use sys.getdefaultencoding() instead?)
    # some email addresses are incorrectly formatted in the original thunderbird address book, try to repair them
    # Note: empty addresses can be either errors or undisclosed-recipients, if you want to diff
    try:
      addresses.append(repair_address(" ".join(x[0] for x in email.header.decode_header(to[1])).lower().strip()))
    except UnicodeEncodeError:
      print(to[1])
  return set(addresses)

  
def main():
  """ The main function that runs this program. First a mapping is created over all input files that are
      captured via the *.csv glob filter. Then a directory called anon is created and each csv file is 
      anonymized according to the mapping. The results are stored in the newly created folder. """
  index = 1
  mapping = {}
  files = glob("*.csv")
  for file in files:
    index = add_to_mapping(mapping, index, parse_csv_to_unique_addresses(file))
  print("mapped %d (%d) addresses." % (len(mapping), index-1))

  if not os.path.isdir("anon"):
    os.makedirs("anon")

  for file in files:
    process(mapping, file)
  print("processed %d files." % len(files))

  with open(os.path.join("anon", "mapping.csv"), 'wb') as wp:
      writer = csv.writer(wp, delimiter=',', quotechar='"')
      for kv in mapping.items():
        writer.writerow(kv)
  print("saved mapping as %s" % os.path.join("anon", "mapping.csv"))


if __name__ == "__main__":
  """ magic main. """
  main()
