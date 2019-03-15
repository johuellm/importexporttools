# Python scripts

The script `ol-extract.py` uses [libff](https://github.com/libyal/libpff) python-bindings to traverse an outlook pst-file and extracts the inbox emails. Because the python-bindings are still work in progress and do not include all necessary means to fully export the recipients of the pst file, the script `ol-transform.py` builds on top of the pffexport tool (also in libpff) and parses its output into a format that is compatible with the `transform.py` script.

The script `transform.py` anonymizes the exported CSV overview.
