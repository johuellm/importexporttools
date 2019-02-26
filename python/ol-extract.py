#!/usr/bin/python3
# -*- coding: utf-8 -*-
# author: Joschka Hüllmann <huellmann@uni-muenster.de>

import os.path
import pypff
import email
import email.header
import email.utils
import email.parser
import unicodecsv as csv

TARGETS_INBOX = (
  # "/Stamm - Postfach/IPM_SUBTREE/Deleted Items/Ordner1",
  # "/Stamm - Postfach/IPM_SUBTREE/Deleted Items/Ordner2",
  # "/Stamm - Postfach/IPM_SUBTREE/Inbox",
  #"/Oberste Ebene der Outlook-Datendatei/Inbox",
  
)

TARGETS_SENT = (
  "/Oberste Ebene der Outlook-Datendatei/Sent Items",
)


def process_message(rows, message, path):

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
  if folder.name != None:
    print("%s%s" % ((" "*depth), folder.name.encode("utf-8")))
  for item in folder.sub_folders:
    show_folders(item, depth+1)


if __name__ == "__main__":
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
