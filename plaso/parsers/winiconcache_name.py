# -*- coding: utf-8 -*-
"""Parser for Windows IconCache.db files."""

from __future__ import unicode_literals

from dfdatetime import semantic_time as dfdatetime_semantic

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager

class WinIconcacheNameExecutionEventData(events.EventData):
  """Windows IconCache.db event data.

  Attributes:
      icon_name (str): icon file name
  """

  DATA_TYPE = 'windows:iconcache:name:execution'

  def __init__(self):
    """Initializes event data."""
    super(WinIconcacheNameExecutionEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.icon_info = None

class WinIconcacheNameParser(interface.FileObjectParser):
  """A parser for Windows IconCache.db: name files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'iconcache_name'
  DESCRIPTION = 'Parser for Windows IconCache.db files.'

  _LEN_SIG = [ b'\x02', b'\x22', b'\42' ]
  _LEN_2_SIG = [ b'\x01', b'\x10', b'\x41', b'\x81', b'\x91', b'\xa1', b'\xc1']
  _HEX_MAP = {'0':0, '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'a':10, 'b':11, 'c':12, 'd':13, 'e':14, 'f':15}

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'\x57\x69\x6e\x34', offset=4)
    return format_specification

  def _openBF(self, file_name):
    fn = file_name
    fh = open(fn, 'rb')
    return fh

  def _readB(self, fh, offset):
    ss = ''
    ss = fh.read(offset)
    if ss == '': return ''
    return ss

  def _closeBF(self, fh):
    fh.close()

  def _calculLen(self, bData):
    strLen = str(hex(int(ord(bData[1]))))[2:] + str(hex(int(ord(bData[0]))))[2:]
    cnt = 0
    sLen = 0
    for c in reversed(strLen):
      sLen += self._HEX_MAP[c] * (16**cnt)
      cnt += 1
    return sLen

  def _getName(self, bData):
    data = ''
    for b in bData:
      if b != b'\x00':
        data += b
    return data

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Iconcache file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    event_data = WinIconcacheNameExecutionEventData()
    date_time = dfdatetime_semantic.SemanticTime('Not set')

    file_object.seek(0)

    #HEADER - unused
    data = file_object.read(64)
    #CNT
    data = file_object.read(2)
    #UnknownData
    data = file_object.read(6)
    data = file_object.read(4)

    #DATA
    while True:
      if data == '': break
      data = file_object.read(4)
      sign = data[:2]
      sLen = self._calculLen(data[2:])
      if sign[0] in self._LEN_2_SIG:
        sLen *= 2
      data = file_object.read(sLen)

      if sign[0] in self._LEN_2_SIG:
        event_data.icon_info = self._getName(data)
        event = time_events.DateTimeValuesEvent(date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
        parser_mediator.ProduceEventWithEventData(event, event_data)
      file_object.read(4)

manager.ParsersManager.RegisterParser(WinIconcacheNameParser)
