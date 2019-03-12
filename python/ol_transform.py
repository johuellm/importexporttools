#!/usr/bin/python3
# -*- coding: utf-8 -*-
# author: Joschka Hüllmann <huellmann@uni-muenster.de>

""" ol_transform.py: This module parses the results of the libpff's pffexport and
                     two csv files of all the directory and contents. One for the
                     sent emails and one for the received emails. The resulting
                     csv files contain an id, sender, recipients and timestamp. """

import pypff
import pytz
import unicodecsv as csv

from datetime import datetime
import email
import email.header
import email.utils
import email.parser
import os
import os.path
import subprocess
import sys


TARGET_ROOT_FOLDER = "backup.pst.export"

TARGETS_INBOX = (
  # os.path.join("Oberste Ebene der Outlook-Datendatei", "Inbox"),
)

TARGETS_SENT = (
  # os.path.join("Oberste Ebene der Outlook-Datendatei", "Sent Items"),
)


def process_transport_headers(filename):
  """ Extracts subject, from, to and formatted date from a textfile that contains transport headers.

      Args:
        filename: The filename of the transport headers file.
      Return:
        A 4-tuple consisting of subject, from, date, list(recipients). """
  subject, source, time = "", "", ""
  with open(filename, "r") as fp:
    headers = email.parser.Parser().parsestr(fp.read(), True)
  if headers["To"] == None: headers["To"] = ""
  if headers["CC"] == None: headers["CC"] = ""
  # We only need comma if both are not empty
  if len(headers["CC"]) > 0 and len(headers["To"]) > 0:
    recipients = headers["To"] + "," + headers["CC"]
  else: 
    recipients = headers["To"] + headers["CC"]
  return headers["Subject"], headers["From"], datetime.strptime(headers["Date"], "%a, %d %b %Y %H:%M:%S %z").strftime("%b %d, %Y %H:%M:%S.%f000 UTC%z"), [(recipients.replace("\r\n","").replace("\n",""), "SMTP"),]
 

def process_headers(filename):
  """ Extracts subject, from, and formatted date from a textfile that contains outlook headers.

    Args:
      filename: The filename of the outlook headers file.
    Return:
      A 3-tuple consisting of subject, from, date. """
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
  """ Extracts list of recipients from a textfile that contains outlook recipients.

    Args:
      filename: The filename of the outlook recipients file.
    Return:
      A list of 2-tuples each consisting of (address, addresstype). """
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
  """ Retrieves a row entry out of an outlook item folder. Each folder represents an item, and 
      the data of the item is stored in various files, e.g. InternetHeaders, OutlookHeaders,
      Meeting or Recipients. OutlookHeaders are always present. Recipients are present if
      the item was transmitted to the inbox or others. InternetHeaders is present only
      if it is an item from the inbox, as sent items do not contain InternetHeaders. Meeting is
      present if the item is a meeting. Data from all these files is extracted and aggregate to
      create a row entry, which includes subject, source, time and list of recipients of an item.

    Args:
      filename: The folder name of the item.
    Return:
      A 4-tuple consisting of subject, from, date, list(recipients). """
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
  """ Old method, that looks up a single item entry and adds 
  """
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
  """ This methods takes a list of unresolved legacyExchangeDns and saves them to a temporary file.
      The temporary file is pushed to a powershell script that invokes the Cmdlet Get-ADObject to
      try and retrieve the email address from the default active directory. Powershell and the 
      Active Directory Remote Administration Tools (e.g. WindowsTH-RSAT_WS_1803-x64.msu) are required.
      The addresses are resolved in the hardcoded file active-directory.csv. First column is the
      legacyExchangeDn, second column is the email address if available.

    Args:
      unresolved_entries: The list of legacyExchangeDns
    Return:
      None """

  # Note: filename is hardcoded in parameter list as well.
  with open("active-directory.new.csv.temp", "w") as fp:
    for entry in unresolved_entries:
      fp.write("%s\n" % entry)

  ps_command_param = """Get-Content .\\active-directory.new.csv.temp | ForEach-Object { Get-ADObject -Filter {legacyExchangeDN -eq $_ } -Property legacyExchangeDN,mail | Select-Object legacyExchangeDN,mail} | Export-Csv active-directory.csv -Append -NoTypeInformation"""
  ps_command = ["powershell.exe", ps_command_param]
  p = subprocess.Popen(ps_command, stdout=subprocess.PIPE)
  p.communicate()


def resolve_legacyexchangedn(rows):
  """ Resolves the legacyExchangeDn to email address for all rows. It uses a prefetched ActiveDirectory
      lookup file hardcoded as active-directory.csv. First column is the legacyExchangeDn, second column
      is the email address if available. The resolve cache is loaded from that prefetched file. Missing
      entries are then aggregated and fetched via powershell and the Get-ADObject Cmdlet; the resolve
      cache is refreshed. Then the lookup is performed. Missing entries are not substituted.

    Args:
      rows: the list of rows to perform lookup on.

    Return:
      None. The parameter is mutated. """

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
  """ Old method, that looks up the emails for all entries in rows. 
  """
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
  """ Concatenates the email part of the recipients tuple, and asserts correct type.
    Args:
      recipients: The list of recipient tuples.
    Return:
      A comma-separated string of recipients' emails. """
  recipients_str = []
  for recipient in recipients:
    if not isinstance(recipient,tuple) or len(recipient) != 2:
      raise TypeError("Probably an error and 2-tuple should be here.")
    recipients_str.append(recipient[0])
  return ",".join(recipients_str)


def get_format_date(datestr):
  """ Parses an input datestring to a timezone aware datetime object and then
      formats it as an UTC string. It can handle strings of the form:

      Feb 06, 2019 09:41:44.223645200 UTC+01:00
      Feb 06, 2019 09:41:44.223645200 UTC+0100
      Feb 06, 2019 09:41:44.223645200 UTC

      The strings are found in the Outlook message and item files.

    Args:
      datestr: The input date string.
    Return:
      A date formatted string in the form of 2019-02-06 09:41:44 in UTC. """

  # Outlook presents headers that cannot be parsed by python, they look like this:
  # Feb 20, 2019 09:04:50.884749100 UTC+01:00  (the +01:00 may also be absent)
  # What we do:
  #   - remove the colon in timezone string (this behavior/format was changed in python 3.7) 
  #   - remove nanoseconds
  # TODO: Does only work with UTC and zero-padded digits.
  source_format = "%b %d, %Y %H:%M:%S.%f %Z%z"
  target_format = "%Y-%m-%d %H:%M:%S"
  if len(datestr) == 41 and datestr[-9:-6] == "UTC" and datestr[-3:-2] == ":":
    if sys.version_info[0] > 2 and sys.version_info[1] > 6:
      pass
    else:
      datestr = datestr[:-13] + datestr[-10:-3] + datestr[-2:]
  elif len(datestr) == 40 and datestr[-8:-5] == "UTC":
    # Note, this is what we parse from internet headers
    datestr = datestr[:-12] + datestr[-9:]
  elif len(datestr) == 35 and datestr[-3:] == "UTC":
    datestr = datestr[0:-7] + datestr[-4:] + "+0000"
  else:
    raise ValueError("Not a date we can parse at this point: %s." % datestr)

  # TODO: Test this better... Datetime hell.
  #       So, by using %Z we always get a time aware datetime object and can use
  #       astime with pytz.utc to convert it to UTC and then format the string.
  dt = datetime.strptime(datestr, source_format)
  if dt.tzinfo == None:
    raise ValueError("This should not happen, error with missing timezone aware datetime object.")
  dt = dt.astimezone(pytz.utc)
  return dt.strftime(target_format)


def write_csv(rows, filename):
  """ Writes the rows to the given file.
    Args:
      rows: the list of rows.
      filename: the output filename.
    Return:
      None.
  """
  with open(filename, "wb") as fp:
    writer = csv.writer(fp, delimiter=',', quotechar='"')
    for row in rows:
      # from (subject, source, time, recipients) to (subject, source, recipients, date)
      try:
        writer.writerow([row[0], row[1], get_recipients_str(row[3]), get_format_date(row[2])])
      except ValueError:
        print(row)
        raise


def process_folder_set(root_folder, folder_set, name):
  """ Processes a set of folders that are exported from pffexport tools.
    Args:
      root_folder: The root folder to start looking into.
      folder_set: The list of folder paths relative to root folder to include in the search and process.
      name: The name of the output file.
    Return:
      None. """
  rows = []
  for folder in folder_set:
    for filename in os.listdir(os.path.join(root_folder,folder)):
      row = create_row(os.path.join(root_folder,folder,filename))
      if row == ["", "", "", []]:
        # None if the required files were found, so probably not an item folder.
        continue
      rows.append(row)

  resolve_legacyexchangedn(rows)

  write_csv(rows, name)


if __name__ == "__main__":
  """ magic main. """
  root_folder = TARGET_ROOT_FOLDER
  process_folder_set(root_folder, TARGETS_SENT, "target.sent.csv")
  process_folder_set(root_folder, TARGETS_INBOX, "target.inbox.csv")
