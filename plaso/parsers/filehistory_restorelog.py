# -*- coding: utf-8 -*-
"""Parser for the FileHistory Restore.log files."""

from __future__ import unicode_literals

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import text_parser

class FileHistoryRestoreLogEventData(events.EventData):
    """Windows FileHistory event data.

    Attributes:
        filerecordid (str):
        restoredfile (str):
        usn (str):
        creationdate (str):
        modificationdate(str):
    """
    DATA_TYPE = 'filehistory:restore:event'

    def __init__(self):
        """Initialize event data"""
        super(FileHistoryRestoreLogEventData, self).__init__(data_type=self.DATA_TYPE)
        self.file_record_id = ''
        self.restored_file = ''
        self.usn = ''
        self.creation_date = ''
        self.modification_date = ''

class FileHistoryRestoreLogParser(interface.FileObjectParser):
    """Parses Windows FileHistory Restore.log file-like object"""

    NAME = 'filehistory_restore'
    DESCRIPTION = 'Parsers for Windows filehistory Restore.log files.'
    _ENCODING = 'utf-8'

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses an Windows FileHistory Restore.log file-like object.

        Args:
            parser_mediator (ParseMediator): mediates interactions between parsers
                and other components, such as storage and dfvfs.
            key (str):
            structure (pyparsing.ParseResults):

        Raises:
            ParseError: when the structure type is unknown.
        """
        event_data = FileHistoryRestoreLogEventData()
        encoding = self._ENCODING or parser_mediator.codepage

        text_file_object = text_parser.text_file.TextFile(file_object, encoding=encoding)
        line = ''
        try:
            line = text_file_object.readline(400)

        except UnicodeDecodeError:
            errors.UnableToParseFile('Not a text file or encoding not supported')

        if not line:
            raise errors.UnableToParseFile('Not a text file.')

        if not line.startswith("<"):
            raise errors.UnableToParseFile('Not an Windows FileHistory Restore.log file.')

        split_line = line.split(' ')
        len_split_line = len(split_line)
        if len_split_line is not 8:
            raise errors.UnableToParseFile('Not an Windows FileHistory Restore.log file.')

        event_data.file_record_id = int(split_line[2].replace("\x00", ""), 16)
        event_data.restored_file = split_line[3].replace("\x00", "")
        event_data.usn = int(split_line[4].replace("\x00", ""), 16)
        temp_creation_date = int(split_line[6].replace("\x00", ""), 16)
        event_data.creation_date = dfdatetime_filetime.\
            Filetime(timestamp=temp_creation_date).CopyToDateTimeString()
        temp_modification_date = int(split_line[7].replace("\x00", "")[:-2], 16)
        event_data.modification_date = dfdatetime_filetime.\
            Filetime(timestamp=temp_modification_date).CopyToDateTimeString()

        date_time = dfdatetime_posix_time.PosixTime(timestamp=0)
        event = time_events.DateTimeValuesEvent(date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
        parser_mediator.ProduceEventWithEventData(event, event_data)

manager.ParsersManager.RegisterParser(FileHistoryRestoreLogParser)