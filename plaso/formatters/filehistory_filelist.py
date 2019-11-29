# -*- coding: utf-8 -*-
"""The file history ESE database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class FileHistoryNamespaceEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a file history ESE database namespace table record."""

  DATA_TYPE = 'filehistory:namespace:event'

  FORMAT_STRING_PIECES = [
      'Backuped Timestamp: {backuped_date_timestamp}',
      'Filename: {full_filepath}',
      'Attributes: {file_attribute}',
      'USN number: {usn_number}',
      'Creation Date: {created_timestamp}',
      'Modification Date: {modified_timestamp}',
      'Filesize: {file_size}',
      'FileRecordId: {file_recordid}']

  FORMAT_STRING_SHORT_PIECES = [
      'Filename: {full_filepath}']

  SOURCE_LONG = 'FileHistory Backup File List'
  SOURCE_SHORT = 'BACKUP'


manager.FormattersManager.RegisterFormatter(FileHistoryNamespaceEventFormatter)
