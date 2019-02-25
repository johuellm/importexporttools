#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: Joschka Hüllmann <huellmann@uni-muenster.de>

from datetime import datetime
import os
import os.path
import pypff
import email
import email.header
import email.utils
import email.parser
import unicodecsv as csv
import subprocess


TARGET_ROOT_FOLDER = "backup-simon.pst.export"

TARGETS_INBOX = (
  # "/Stamm - Postfach/IPM_SUBTREE/Deleted Items/Ordner1",
  # "/Stamm - Postfach/IPM_SUBTREE/Deleted Items/Ordner2",
  # "/Stamm - Postfach/IPM_SUBTREE/Inbox",
  # os.path.join("Oberste Ebene der Outlook-Datendatei", "Inbox"),
  os.path.join("Top of Outlook data file", "Posteingang"),
  
)

TARGETS_SENT = (
  # os.path.join("Oberste Ebene der Outlook-Datendatei", "Sent Items"),
  os.path.join("Top of Outlook data file", "Gesendete Elemente"),
)


def process_transport_headers(filename):
  subject, source, time = "", "", ""
  with open(filename, "r") as fp:
    headers = email.parser.Parser().parsestr(fp.read(), True)    
  if headers["To"] == None: headers["To"] = ""
  return headers["Subject"], headers["From"], datetime.strptime(headers["Date"][:-6], "%a, %d %b %Y %H:%M:%S").strftime("%b %d, %Y %H:%M:%S.000000000 UTC"), [(headers["To"].replace("\r\n",""), "SMTP"),]
 

def process_headers(filename):
  subject, source, time = "", "", ""
  with open(filename, "r") as fp:
    lines = fp.readlines()
    for line in lines:
      if line.startswith("Subject:"):
        subject = line[len("Subject:"):].strip()
      elif line.startswith("Sender email address:"):
        source = line[len("Sender email address:"):].strip()
      elif line.startswith("Delivery time:"):
        time = line[len("Delivery time:"):].strip()
  return subject, source, time


def process_recipients(filename):
  recipients = []
  with open(filename, "r") as fp:
    lines = fp.readlines()
    # always read until empty line
    email = ""
    email_type = ""
    for line in lines:
      if line.strip() == "":
        recipients.append((
          email,
          email_type
        ))
      elif line.startswith("Email address:"):
        email = line[len("Email address:"):].strip()
      elif line.startswith("Address type:"):
        email_type = line[len("Address type:"):].strip()

  return recipients


def create_row(filename):
  if not os.path.isdir(filename):
    return
  (subject, source, time, recipients) = ("", "", "", [])
  if os.path.isfile(os.path.join(filename,"InternetHeaders.txt")):
    return list(process_transport_headers(os.path.join(filename,"InternetHeaders.txt")))
  elif os.path.isfile(os.path.join(filename,"OutlookHeaders.txt")):
    (subject, source, time) = process_headers(os.path.join(filename,"OutlookHeaders.txt"))
  elif os.path.isfile(os.path.join(filename,"Meeting.txt")):
    (subject, source, time) = process_headers(os.path.join(filename,"Meeting.txt"))
  if os.path.isfile(os.path.join(filename,"Recipients.txt")):
    recipients = process_recipients(os.path.join(filename,"Recipients.txt"))
  return [subject, source, time, recipients]


def resolve_legacyexchangedn_lookup_old(entry, resolve_cache):
  if entry[1] == "EX":
    legacyExchangeDN = entry[0].lower()
    if legacyExchangeDN in resolve_cache:
      return (resolve_cache[legacyExchangeDN], "SMTP")
    
    ps_command = ["powershell.exe", "-command"]
    ps_filter_template = "Get-ADObject -Filter {{legacyExchangeDN -eq '{0}'}} -Properties mail | foreach {{ $_.mail }}"
    p = subprocess.Popen(ps_command + [ps_filter_template.format(entry[0]),], stdout=subprocess.PIPE)
    email, _ = p.communicate()
    email = email.strip().lower()
    resolve_cache[legacyExchangeDN] = email
    return (email, "SMTP")
  else:
    return entry


def refresh_resolve_cache(unresolved_entries):

  # Note: filename is hardcoded in parameter list as well.
  with open("active-directory.new.csv.temp", "w") as fp:
    for entry in unresolved_entries:
      fp.write("%s\n" % entry)

  ps_command_param = """Get-Content .\\active-directory.new.csv.temp | ForEach-Object { Get-ADObject -Filter {legacyExchangeDN -eq $_ } -Property legacyExchangeDN,mail | Select-Object legacyExchangeDN,mail} | Export-Csv active-directory.csv -Append -NoTypeInformation"""
  ps_command = ["powershell.exe", ps_command_param]
  p = subprocess.Popen(ps_command, stdout=subprocess.PIPE)
  p.communicate()


def resolve_legacyexchangedn(rows):

  # Prefetch command
  # Get-ADUser -f {name -like "*"} -Property legacyExchangeDn,mail | Select-Object legacyExchangeDn,mail | Export-Csv OUTPUT.csv

  # (1) Load pre-fetched active directory lookup table
  resolve_cache = {}
  with open("active-directory.csv", 'rb') as fp:
    reader = csv.reader(fp, delimiter=',', quotechar='"')
    next(reader) # skip header
    for row in reader:
      if row[0].strip() != "" and row[1].strip() != "":
        resolve_cache[row[0].strip().lower()] = row[1].strip().lower()

  # (2) Write unresolved names into file for powershell script
  unresolved_entries = []
  for row in rows:
    # resolve sender, here we do not know if it is email or legacyexchangeDn, so we infer it via @
    if row[1].lower() not in resolve_cache and row[1].lower() not in unresolved_entries and "@" not in row[1]:
      unresolved_entries.append(row[1].lower())
    # resolve recipients
    for recipient in row[3]:
      if recipient[1] == "EX" and recipient[0].lower() not in resolve_cache and recipient[0].lower() not in unresolved_entries:
        unresolved_entries.append(recipient[0].lower())

  refresh_resolve_cache(unresolved_entries)
  os.remove("active-directory.new.csv.temp")

  # (3) reload cache
  resolve_cache = {}
  with open("active-directory.csv", 'rb') as fp:
    reader = csv.reader(fp, delimiter=',', quotechar='"')
    next(reader) # skip header
    for row in reader:
      if row[0].strip() != "" and row[1].strip() != "":
        resolve_cache[row[0].strip().lower()] = row[1].strip().lower()

  # (4) do the look up
  for row in rows:
    # resolve recipients
    resolved_recipients = []
    for recipient in row[3]:
      if recipient[1] == "EX" and recipient[0].lower() in resolve_cache:
        resolved_recipients.append((resolve_cache[recipient[0].lower()], "SMTP"))
      else:
        resolved_recipients.append(recipient)
    row[3] = resolved_recipients
    # and try-resolve sender
    if row[1].lower() in resolve_cache:
      row[1] = resolve_cache[row[1].lower()]


def resolve_legacyexchangedn_old(rows):
  resolve_cache = {}
  for row in rows:
    # resolve recipients
    resolved_recipients = []
    for recipient in row[3]:
      resolved_recipients.append(resolve_legacyexchangedn_lookup(recipient, resolve_cache))
    row[3] = resolved_recipients
    # and resolve sender
    row[1] = resolve_legacyexchangedn_lookup((row[1], "EX"), resolve_cache)[0]


def get_recipients_str(recipients):
  recipients_str = []
  # recipients_template = '"{0}"'
  for recipient in recipients:
    recipients_str.append(recipient[0])
    # recipients_str.append(recipients_template.format(recipient[0]))
  return ",".join(recipients_str)


def get_format_date(datestr):
  datestr = datestr[0:-7]
  source_format = "%b %d, %Y %H:%M:%S.%f"
  target_format = "%d.%m.%Y %H:%M"
  return datetime.strptime(datestr, source_format).strftime(target_format)


def write_csv(rows, filename):
  with open(filename, "wb") as fp:
    writer = csv.writer(fp, delimiter=',', quotechar='"')
    for row in rows:
      # from (subject, source, time, recipients) to (subject, source, recipients, date)
      writer.writerow([row[0], row[1], get_recipients_str(row[3]), get_format_date(row[2])])


def process_folder_set(root_folder, folder_set, name):
  rows = []
  for folder in folder_set:
    for filename in os.listdir(os.path.join(root_folder,folder)):
      row = create_row(os.path.join(root_folder,folder,filename))
      rows.append(row)

  resolve_legacyexchangedn(rows)

  write_csv(rows, name)


if __name__ == "__main__":
  root_folder = TARGET_ROOT_FOLDER
  process_folder_set(root_folder, TARGETS_SENT, "target.sent.csv")
  process_folder_set(root_folder, TARGETS_INBOX, "target.inbox.csv")
