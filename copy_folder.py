#!/usr/bin/python
import argparse
import os.path
import sys

# Find patched bleach module
sys.path.append(os.path.join(os.path.dirname(__file__), '../bleach'))

from gdrivepel.downloader import GDriveDownloader

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Recursively downloads the contents of a Google Drive folder to a path on the local machine')
    parser.add_argument('-v', '--verbose', action='store_true', help='print progress on stdout')
    parser.add_argument('-n', '--stats_only', action='store_true', help='get statistics (no downloading)')
    parser.add_argument('src_folder_id', metavar='SRC_FOLDER_ID', help='top level Google Drive folder id')
    parser.add_argument('dest_base', metavar='DEST_BASE', help='top level path')

    args = parser.parse_args()
    downloader = GDriveDownloader(verbose=args.verbose, stats_only=args.stats_only)
    downloader.recursiveDownloadInto(args.src_folder_id, args.dest_base)
    downloader.postProcess()
