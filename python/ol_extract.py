#!/usr/bin/python3
# -*- coding: utf-8 -*-
# author: Joschka Hüllmann <huellmann@uni-muenster.de>

""" ol_extract.py: This module uses the pypff library to show all the entries in the PST file. Since
                   the python bindings are work-in-progres, only meetings and emails are shown. """

import os.path
import pypff
import email
import email.header
import email.utils
import email.parser
import unicodecsv as csv

TARGETS_INBOX = (
  #"/Oberste Ebene der Outlook-Datendatei/Inbox",
  
)

TARGETS_SENT = (
  "/Oberste Ebene der Outlook-Datendatei/Sent Items",
)


def process_message(rows, message, path):
  """ Processes a message and appends to the list of rows as specified by path.
    Args:
      rows: The dict of output files, with each key being an output file and
            each value being a list of rows to append to and write to the
            output file.
      message: The given message to parse.
      path: Is the key, to which list to append. """

  if path in TARGETS_INBOX:
    outfile = "mails.inbox.csv"
  elif path in TARGETS_SENT:
    outfile = "mails.sent.csv"
  else:
    outfile = "mails.what.csv"

  if message.transport_headers == None:
    return

  headers = email.parser.Parser().parsestr(message.transport_headers, True)

  row = [headers["Subject"], headers["From"], headers["To"], headers["Date"]]
  rows[outfile].append(row)
 

def traverse_folder(rows, folder, path="", depth=0):
  """ Recursively traverses a folder and and appends all found items to the rows dict.
    Args:
      rows: The dict of row lists to append to. 
      folder: The current folder name being traversed. 
      path: The current full path to the folder. 
      depth: The current recursion depth. """
  print("[>] ENTERING %s" % path)
  count = 0
  for item in folder.sub_items:
    if isinstance(item, pypff.message):
      process_message(rows, item, path.strip())
      count = count + 1
    elif isinstance(item, pypff.folder):
      traverse_folder(rows, item, path+"/"+item.name, depth+1)
    else:
      pass
      # print "did not do anything for: %s (type: %s)" % (item.identifier, item.__class__.__name__)
  print("[v] PROCESSED %d MESSAGES" % count)
  print("[<] LEAVING %s" % path)


def show_folders(folder, depth=0):
  """ Shows or prints all folder names recursively.
    Args:
      folder: The top level folder.
      depth: The recursion depth. """
  if folder.name != None:
    print("%s%s" % ((" "*depth), folder.name.encode("utf-8")))
  for item in folder.sub_folders:
    show_folders(item, depth+1)


if __name__ == "__main__":
  """ magic main. """
  pff_file = pypff.open("backup.pst")

  show_folders(pff_file.root_folder)

  try:
    root = pff_file.root_folder
    rows = {"mails.inbox.csv": [],
            "mails.sent.csv": [],
            "mails.what.csv": []}

    traverse_folder(rows, root, "")

    for file,entries in rows.items():
      with open(os.path.join("", file), 'wb') as wp:
        writer = csv.writer(wp, delimiter=',', quotechar='"')
        for entry in entries:
          writer.writerow(entry)

    
  finally:
    pff_file.close()
