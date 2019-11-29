# -*- coding: utf-8 -*-
"""Parser for Global table of the Microsoft File History ESE database."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface

class FileHistoryGlobalEventData(events.EventData):
    """File History global table event data.

    Attributes:
        first_backup_timestamp (str):
        last_backup_timestamp (str):
    """

    DATA_TYPE = 'filehistory:global:event'

    def __init__(self):
        """Initializes event data."""
        super(FileHistoryGlobalEventData, self).__init__(
            data_type=self.DATA_TYPE)
        self.first_backup_timestamp = None
        self.last_backup_timestamp = None

class FileHistoryGlobalTableParser(interface.ESEDBPlugin):
    """Parses a Global Table of File History ESE database file."""

    NAME = 'filehistory_global'
    DESCRIPTION = 'Parser for File History Global Table.'

    REQUIRED_TABLES = {'global': 'ParseGlobal'}

    def _GetDictFromGlobalTable(self, parser_mediator, table):
        """Build a dictionary of the value in the global table.

        Args:
            parser_mediator (ParserMediator):
            table (pyesedb.table): global table.

        Returns:

        """
        if not table:
            return {}

        record_values = {}
        for record in table.records:
            if parser_mediator.abort:
                break

            if record.get_number_of_values() != 3:
                continue

            identification = self._GetRecordValue(record, 0)
            key = self._GetRecordValue(record, 1)
            value = self._GetRecordValue(record, 2)

            if not key:
                continue
            record_values[key] = value

        return record_values

    def ParseGlobal(
            self, parser_mediator, cache=None, database=None, table=None,
            **unused_kwargs):
        """Parses the global table.

        Args:

        """

        if database is None:
            raise ValueError('Missing database value.')

        if table is None:
            raise ValueError('Missing table value.')

        globals = cache.GetResults('globals')
        if not globals:
            esedb_table = database.get_table_by_name('global')
            globals = self._GetDictFromGlobalTable(parser_mediator, esedb_table)
            cache.StoreDictInCache('globals', globals)

        event_data = FileHistoryGlobalEventData()
        temp_first_backup = globals.get('FirstBackupTime')[::-1].hex()
        first_backup_timestamp = int(temp_first_backup, 16)
        temp_last_backup = globals.get('LastBackupTime')[::-1].hex()
        last_backup_timestamp = int(temp_last_backup, 16)

        first_backup_datetime = dfdatetime_filetime.Filetime(timestamp=first_backup_timestamp)
        event_data.first_backup_timestamp = first_backup_datetime.CopyToDateTimeString()

        last_backup_datetime = dfdatetime_filetime.Filetime(timestamp=last_backup_timestamp)
        event_data.last_backup_timestamp = last_backup_datetime.CopyToDateTimeString()

        if first_backup_datetime:
            event = time_events.DateTimeValuesEvent(
                first_backup_datetime, definitions.TIME_DESCRIPTION_BACKUP)
            parser_mediator.ProduceEventWithEventData(event, event_data)

        if last_backup_datetime:
            event = time_events.DateTimeValuesEvent(
                last_backup_datetime, definitions.TIME_DESCRIPTION_BACKUP)
            parser_mediator.ProduceEventWithEventData(event, event_data)

        if not first_backup_datetime and not last_backup_datetime:
            date_time = dfdatetime_semantic_time.SemanticTime('Not set')
            event = time_events.DateTimeValuesEvent(
                date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
            parser_mediator.ProduceEventWithEventData(event, event_data)

esedb.ESEDBParser.RegisterPlugin(FileHistoryGlobalTableParser)