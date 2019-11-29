# -*- coding: utf-8 -*-
"""The Windows FileHistory Restore.log event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class FileHistoryRestoreLogFormatter(interface.ConditionalEventFormatter):
    """Formatter for an Windows FileHistory Restore.log parsing result."""

    DATA_TYPE = 'filehistory:restore:event'

    FORMAT_STRING_PIECES = [
        'FileRecordID: {file_record_id}',
        'Restored File: {restored_file}',
        'USN of File: {usn}',
        'Creation Date: {creation_date}',
        'Modification Date: {modification_date}']

    SOURCE_LONG = 'FileHistory RestoreLog'
    SOURCE_SHORT = 'BACKUP'

manager.FormattersManager.RegisterFormatter(FileHistoryRestoreLogFormatter)