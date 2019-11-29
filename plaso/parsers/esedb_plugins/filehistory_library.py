# -*- coding: utf-8 -*-
"""Parser for library table of the Microsoft File History ESE database."""

from __future__ import unicode_literals

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface

class FileHistoryLibraryEventData(events.EventData):
    """File History library table event data.

    Attributes:
        backup_folder (str):
    """

    DATA_TYPE = 'filehistory:library:event'

    def __init__(self):
        """Initializes event data."""
        super(FileHistoryLibraryEventData, self).__init__(
            data_type=self.DATA_TYPE)
        self.backup_folder = None

class FileHistoryLibraryTableParser(interface.ESEDBPlugin):
    """Parses a Library Table of File History ESE database file."""

    NAME = 'filehistory_library'
    DESCRIPTION = 'Parser for File History Library Table.'

    REQUIRED_TABLES = {'library': 'ParseLibrary'}

    def _GetDictFromStringsTable(self, parser_mediator, table):
        """Build a dictionary of the value in the strings table.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfvfs.
          table (pyesedb.table): strings table.

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
            filename = self._GetRecordValue(record, 1)

            if not identification:
                continue
            record_values[identification] = filename

        return record_values

    def ParseLibrary(
            self, parser_mediator, cache=None, database=None, table=None,
            **unused_kwargs):
        """Parses the library table.

        Args:

        """
        if database is None:
            raise ValueError('Missing database value.')

        if table is None:
            raise ValueError('Missing table value.')

        strings = cache.GetResults('strings')
        if not strings:
            esedb_table = database.get_table_by_name('string')
            strings = self._GetDictFromStringsTable(parser_mediator, esedb_table)
            cache.StoreDictInCache('string', strings)

        backup_folder_list = ""

        event_data = FileHistoryLibraryEventData()
        for esedb_record in table.records:
            if parser_mediator.abort:
                break

            record_values = self._GetRecordValues(
                parser_mediator, table.name, esedb_record)

            parentid = record_values.get('parentId')
            childid = record_values.get('childId')
            backup_folder_list += str(strings.get(parentid)) + "\\" \
                                  + str(strings.get(childid)) + ", "

        event_data.backup_folder = backup_folder_list
        date_time = dfdatetime_java_time.JavaTime(timestamp=0)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
        parser_mediator.ProduceEventWithEventData(event, event_data)


esedb.ESEDBParser.RegisterPlugin(FileHistoryLibraryTableParser)