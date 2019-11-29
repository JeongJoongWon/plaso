# -*- coding: utf-8 -*-
"""The global table of Windows FileHistory event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class FileHistoryGlobalTableFormatter(interface.ConditionalEventFormatter):
    """Formatter for an Windows FileHistory Global Table parsing result."""

    DATA_TYPE = 'filehistory:global:event'

    FORMAT_STRING_PIECES = [
        'First FileHistory Backup: {first_backup_timestamp}',
        'Last FileHistory Backup: {last_backup_timestamp}']

    SOURCE_LONG = 'FileHistory Global'
    SOURCE_SHORT = 'BACKUP'

manager.FormattersManager.RegisterFormatter(FileHistoryGlobalTableFormatter)