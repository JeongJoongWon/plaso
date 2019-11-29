# -*- coding: utf-8 -*-
"""The Windows FileHistory Library Table event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class FileHistoryLibraryFormatter(interface.ConditionalEventFormatter):
    """Formatter for an Windows FileHistory Library Table parsing result."""

    DATA_TYPE = 'filehistory:library:event'

    FORMAT_STRING_PIECES = [
        'BackupFolder: {backup_folder}']

    SOURCE_LONG = 'FileHistory Backup Folder'
    SOURCE_SHORT = 'BACKUP'

manager.FormattersManager.RegisterFormatter(FileHistoryLibraryFormatter)