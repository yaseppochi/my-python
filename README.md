# my-python

This is a diverse group of utility scripts I've written and used heavily at one time or another, and I don't claim the style is very good (although I try to habitually write clear code.

The exception is `myzipfile.py'. I believe this addition, though small, is well-designed and coded in good style. I added the 'filenameencoding' argument to the ZipFile constructor, restricted to read-only because the ZipFile standard mandates file names in ISO-8859-1 or UtF-8. I submitted it for contribution to the Python standard library, but it was not accepted. The file's maintainer wanted to think about rewriting the command line interface to use argparse, but wouldn't let me do that. I was hoping that it wouldn't matter -- the filenameencoding feature would be unnecessary as Japanese learned to use Unicode-aware utilities. But they haven't, and I've used it as recently as last week to unzip a file whose names were encoded in Shift JIS. Eventually I may try again.
