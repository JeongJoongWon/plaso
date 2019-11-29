# -*- coding: utf-8 -*-
"""Parser for the Microsoft File History ESE database."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class FileHistoryNamespaceEventData(events.EventData):
  """File history namespace table event data.

  Attributes:
    file_attribute (int): file attribute.
    identifier (str): identifier.
    original_filename (str): original file name.
    parent_identifier (str): parent identifier.
    usn_number (int): USN number.
  """

  DATA_TYPE = 'filehistory:namespace:event'

  def __init__(self):
    """Initializes event data."""
    super(FileHistoryNamespaceEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.backuped_date = None #tCreated
    self.file_attribute = None
    self.file_size = None
    self.full_filepath = None #parent folder path + original filename
    self.usn_number = None
    self.created_timestamp = None
    self.modified_timestamp = None
    self.file_recordid = None

class FileHistoryNameSpaceParser(interface.ESEDBPlugin):
  """Parses a File History ESE database file."""

  NAME = 'filehistory_filelist'
  DESCRIPTION = 'Parser for File History ESE database files.'

  # TODO: Add support for other tables as well, backupset, file, library, etc.
  REQUIRED_TABLES = {
      'backupset': '',
      'file': '',
      'library': '',
      'namespace': 'ParseNameSpace'}

  def _GetDictFromFileTable(self, parser_mediator, table):
    """Build a dictionary of the value in the file table.

    Args:
      parser_mediator (ParserMediator):
      table (pyesedb.table): file table.

    Returns:

    """
    if not table:
      return {}

    record_values = {}
    for record in table.records:
      if parser_mediator.abort:
        break

      if record.get_number_of_values() != 9:
        continue

      parentId = self._GetRecordValue(record, 1)
      childId = self._GetRecordValue(record, 2)
      fileSize = self._GetRecordValue(record, 5)

      if not childId:
        continue
      record_values[childId] = [fileSize, parentId]

    return record_values

  def _GetDictFromBackupsetTable(self, parser_mediator, table):
    """Build a dictionary of the value in the backupset table.

    Args:
      parser_mediator (ParserMediator):
      table (pyesedb.table): backupset table.

    Returns:

    """
    if not table:
      return {}

    record_values = {}
    for record in table.records:
      if parser_mediator.abort:
        break

      if record.get_number_of_values() != 2:
        continue

      identification = self._GetRecordValue(record, 0)
      timestamp = self._GetRecordValue(record, 1)

      if not identification:
        continue
      record_values[identification] = timestamp

    return record_values

  def _GetDictFromStringsTable(self, parser_mediator, table):
    """Build a dictionary of the value in the strings table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      table (pyesedb.table): strings table.

    Returns:
      dict[str,object]: values per column name.
    """
    if not table:
      return {}

    record_values = {}
    for record in table.records:
      if parser_mediator.abort:
        break

      if record.get_number_of_values() != 2:
        continue

      identification = self._GetRecordValue(record, 0)
      filename = self._GetRecordValue(record, 1)

      if not identification:
        continue
      record_values[identification] = filename

    return record_values

  def ParseNameSpace(
      self, parser_mediator, cache=None, database=None, table=None,
      **unused_kwargs):
    """Parses the namespace table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache (Optional[ESEDBCache]): cache.
      database (Optional[pyesedb.file]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    strings = cache.GetResults('strings')
    if not strings:
      esedb_table = database.get_table_by_name('string')
      strings = self._GetDictFromStringsTable(parser_mediator, esedb_table)
      cache.StoreDictInCache('strings', strings)

    backupsets = cache.GetResults('backupsets')
    if not backupsets:
      esedb_table = database.get_table_by_name('backupset')
      backupsets = self._GetDictFromBackupsetTable(parser_mediator, esedb_table)
      cache.StoreDictInCache('backupsets', backupsets)

    files = cache.GetResults('files')
    if not files:
      esedb_table = database.get_table_by_name('file')
      files = self._GetDictFromFileTable(parser_mediator, esedb_table)
      cache.StoreDictInCache('files', files)

    for esedb_record in table.records:
      if parser_mediator.abort:
        break

      record_values = self._GetRecordValues(
          parser_mediator, table.name, esedb_record)

      event_data = FileHistoryNamespaceEventData()
      backuped_id = record_values.get('tCreated')
      childid = record_values.get('childId')
      parent_identifier = files.get(childid)[1]

      backuped_date = backupsets.get(backuped_id)
      event_data.file_attribute = record_values.get('fileAttrib')
      event_data.file_size = files.get(childid)[0]

      event_data.usn_number = record_values.get('usn')
      event_data.full_filepath = strings.get(parent_identifier) + "\\" + strings.get(childid)
      event_data.file_recordid = record_values.get('fileRecordId')
      created_timestamp = record_values.get('fileCreated')
      modified_timestamp = record_values.get('fileModified')

      if backuped_date:
        backuped_date_time = dfdatetime_filetime.Filetime(timestamp=backuped_date)
        created_date_time = dfdatetime_filetime.Filetime(timestamp=created_timestamp)
        modified_date_time = dfdatetime_filetime.Filetime(timestamp=modified_timestamp)
        event_data.backuped_date_timestamp = backuped_date_time.CopyToDateTimeString()
        event_data.created_timestamp = created_date_time.CopyToDateTimeString()
        event_data.modified_timestamp = modified_date_time.CopyToDateTimeString()
        event = time_events.DateTimeValuesEvent(
            backuped_date_time, definitions.TIME_DESCRIPTION_BACKUP)

      parser_mediator.ProduceEventWithEventData(event, event_data)

esedb.ESEDBParser.RegisterPlugin(FileHistoryNameSpaceParser)