#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: Joschka Hüllmann <huellmann@uni-muenster.de>

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
  addresses = []
  with open(file, 'rb') as fp:
    reader = csv.reader(fp, delimiter=',', quotechar='"')
    for row in reader:
      addresses.append(row[SOURCE])
      addresses.append(row[TARGET])
  return set(addresses)


def process(mapping, file):
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
  # Some email addresses have two extra apostrophes
  if addr.startswith("'") and addr.endswith("'"): return addr[1:-1]
  if addr.startswith('"') and addr.endswith('"'): return addr[1:-1]
  # remove known invalid addresses
  if addr in ('"xxx\\""@xxx.de',): return "invalid-address"
  # else
  return addr


def check_special_addresses(addr):
  # shortcut for undisclosed recipients
  addr = addr.lower().strip()
  if addr in ("undisclosed-recipients:;", "undisclosed recipients:;", "verborgene_empfaenger: ;"):
    return ("undisclosed-recipients", True)
  # else
  return (addr, False)


def split_address(addr):
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
      print to[1]
  return set(addresses)

  
def main():
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
  main()
