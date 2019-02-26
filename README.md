# ImportExportTools

This is a mirror of the ImportExport Tools addon, latest version 3.3.2 (2019-02-04). It is currently maintained by [Paolo "Kaosmos"](https://freeshell.de/~kaosmos/mboximport-en.html) and listed on [addons.thunderbird.net](https://addons.thunderbird.net/de/thunderbird/addon/importexporttools/).

I have implemented several changes to the export overview CSV function, to fix bugs that would screw up the formatting and subsequent processing of the recipients and senders of emails. Find attached below the original description.

I also added three [python scripts](https://github.com/johuellm/importexporttools/tree/master/python): The first `transform.py` anonymizes the exported CSV overview. The script `ol-extract.py` uses [libff](https://github.com/libyal/libpff) python-bindings to traverse an outlook pst-file and extracts the inbox emails. Because the python-bindings are still work in progress and do not include all necessary means to fully export the recipients of the pst file, the script `ol-transform.py` builds on top of the pffexport tool (also in libpff) and parses its output into a format that is compatible with the `transform.py` script.




## About this Add-on

If you don't see here the last version (3.3.2), get it at my [website](https://freeshell.de/~kaosmos/importexporttools-en.html), it should fix the bugs with TB60.

This extension allows the user to export and import folders and messages with lots of options, for example:

Tools Menu --> ImportExportTools or Context menu on folders panel --> Import/Export
- export of folder in a single file (mbox format), with also the subfolders if you want;
- export of all messages in single files (eml or html or plain text format or CSV), with attachments and an index;
- export of all messages in PDF format (required ImportExportTools 3.0 or higher)
- export of all messages in one single plain text file;
- export of index of the messages in a folder (HTML or CSV format);
- mbox files import;
- eml files import;
- emlx files import;
- import of all the eml files existing in a directory;
- export of all files of all mail files of the profile (just from the "Tools" menu);
- import of a saved profile (just from the "Tools" menu, required ImportExportTools 3.0 or higher, not available for Seamonkey)
- search with various criteria and export messages;
- import SMS from the programs "SMS Backup and Restore" for Android and Nokia2AndroidSMS;

File menu --> Save selected messages or Context menu of thread panel --> Save selected messages
- saving multiple messages in eml/html/plain text format with just one click;
- saving multiple messages in PDF format with just one click (required ImportExportTools 3.0 or higher)

Message menu --> Copy to clipboard or Context menu of thread panel --> Copy to clipboard
- copy the message or all headers to clipboard.

Context menu on an EML attachment
- import file in the folder

ImportExportTools can also perform a scheduled backup of all profile's files or just of mail files and NOW CAN IMPORT A SAVED PROFILE (required ImportExportTools 3.0 or higher, not available for Seamonkey)

Note: if you want to import messages or MBOX files, you must first select a valid folder as a target, otherwise the import options are disabled

For more details visit https://freeshell.de/~kaosmos/mboximport-en.html

In my website you can find lots of extensions and maybe some of them could interest you, so have a peek.

To contact me, please use my email address in my homepage.
If you want to make a donation for my work, you can find the link in my webpage.
