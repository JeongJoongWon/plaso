# -*- coding: utf-8 -*-
"""Parser for Windows WinSearchDB files."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions

from datetime import datetime as dt
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface

class WinSearchDBExecutionEventData(events.EventData):
  """Windows WinSearchDB event data.

  Attributes:

  """

  DATA_TYPE = 'windows:searchdb:execution'

  def __init__(self):
    """Initializes event data."""
    super(WinSearchDBExecutionEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.ID = None
    self.Name = None
    self.Owner = None
    self.IURL = None
    self.IAttr = None
    self.IsFolder = None
    self.Size = None
    self.GatherDT = None
    self.ModifyDT = None
    self.AccessDT = None
    self.SUMMARY = None
    self.Title = None
    self.Subject = None
    self.Comment = None
    self.Label = None
    self.Text = None
    self.APPName = None

class WinSearchESEDBPlugin(interface.ESEDBPlugin):
  """A parser for Windows Search DB files."""

  NAME = 'winsearchdb'
  DESCRIPTION = 'Parser for Windows SearchDB files.'

  REQUIRED_TABLES = {
   'SystemIndex_PropertyStore': 'ParseWinSearchDB'
#    'SystemIndex_0A': 'ParseWinSearchDB'
  }

  HEX_MAP = {"0":0, "1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7, "8":8, "9":9, "a":10, "b":11, "c":12, "d":13, "e":14, "f":15}

  _TARGET_COLUMNS = ['WorkID', 'System_FileName', 'System_FileOwner', 'System_ItemUrl', 'System_FileAttributes',
                    'System_IsFolder', 'System_Size', 'System_Search_GatherTime', 'System_DateCreated', 'System_DateModified', 'System_DateAccessed',
                    'System_Search_AutoSummary', 'System_Title', 'System_Subject', 'System_Comment', 'System_Contact_Label', 'System_PriorityText',
                    'System_ApplicationName']
  _COLUMN2PRINT = {"ID":"WorkID", "Name":"System_FileName", "IType":"System_ItemTypeText", "Owner":"System_FileOwner", "IURL":"System_ItemUrl",
                  "IAttr":"System_FileAttributes", "IsFolder":"System_IsFolder", "Size":"System_Size", "GatherDT":"System_Search_GatherTime",
                  "CreateDT":"System_DateCreated", "ModifyDT":"System_DateModified", "AccessDT":"System_DateAccessed",
                  "SUMMARY":"System_Search_AutoSummary", "Title":"System_Title", "Subject":"System_Subject", "Comment":"System_Comment",
                  "Label":"System_Contact_Label", "Text":"System_PriorityText", "APPName":"System_ApplicationName" }
  
  def _ldap2unix(self, ldap):
    uSecs = ldap/10000000
    uTimestamp = uSecs - 11644473600
    return uTimestamp
  
  def _GetSize(self, bData):
    if ord(bData[0]) == ord(bData[1]) == ord(bData[2]) == ord(bData[3]) == ord(bData[4]) == ord(bData[5]) == ord(bData[6]) == ord(bData[7]) == 42:
      return 0
  
    size = 0
    idx = 0
    for b in bData:
      if len(hex(ord(b))) == 4:
        tens=self.HEX_MAP[hex(ord(b))[3]]
        size += tens*(16**idx)
        idx += 1
        units=self.HEX_MAP[hex(ord(b))[2]]
        size += units*(16**idx)
        idx += 1
      else:
        units=self.HEX_MAP[hex(ord(b))[2]]
        size += units*(16**idx)
        idx += 2
    return size

  def ParseRecords(self, parser_mediator, database, table):
    win_ret = []
    for record in table.records:
      record_values = self._GetRecordValues(parser_mediator, table.name, record)
      cmn = record_values.keys()
      cmn_ret = {"WorkID":"", "System_FileName":"", "System_FileOwner":"", "System_ItemUrl":"", "System_FileAttributes":"",
                 "System_IsFolder":"", "System_Size":"", "System_Search_GatherTime":"", "System_DateCreated":"", "System_DateModified":"",
                 "System_DateAccessed":"", "System_Search_AutoSummary":"", "System_Title":"", "System_Subject":"", "System_Comment":"", "System_Contact_Label":"",
                 "System_PriorityText":"", "System_ApplicationName":"" }
      for c in cmn:
        for s_cmn in self._TARGET_COLUMNS:
          if s_cmn in c[len(c)*-1:]:
            cmn_ret[s_cmn] = record_values[c]
      win_ret.append(dict(cmn_ret))
    return win_ret

  def ParseWinSearchDB(self, parser_mediator, cache=None, database=None, table=None,
      **unused_kwargs):
    """Parses a Windows Windows Search DB file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    win_ret = self.ParseRecords(parser_mediator, database, table)
    for ret in win_ret:
      event_data = WinSearchDBExecutionEventData()
      event_data.ID = str(ret[self._COLUMN2PRINT["ID"]])

      if ret[self._COLUMN2PRINT["Name"]] is not None:
        event_data.Name = ret[self._COLUMN2PRINT["Name"]].encode('utf-8')
      else:
        event_data.Name = 'None'
      if ret[self._COLUMN2PRINT["Owner"]] is not None:
        event_data.Owner = ret[self._COLUMN2PRINT["Owner"]].encode('utf-8')
      else:
        event_data.Owner = 'None'
      if ret[self._COLUMN2PRINT["IURL"]] is not None:
        event_data.IURL = ret[self._COLUMN2PRINT["IURL"]].encode('utf-8')
      else:
        event_data.IURL = 'None'

      event_data.IAttr = str(ret[self._COLUMN2PRINT["IAttr"]])
      event_data.IsFolder = str(ret[self._COLUMN2PRINT["IsFolder"]])
      event_data.Size = str(self._GetSize(ret[self._COLUMN2PRINT["Size"]]))
      if self._GetSize(ret[self._COLUMN2PRINT["GatherDT"]]) == 0:
        event_data.GatherDT = str(0)
      else:
        event_data.GatherDT = str(dt.utcfromtimestamp(self._ldap2unix(self._GetSize(ret[self._COLUMN2PRINT["GatherDT"]]))))

      if self._GetSize(ret[self._COLUMN2PRINT["ModifyDT"]]) == 0:
        event_data.ModifyDT = str(0)
      else:
        event_data.ModifyDT = str(dt.utcfromtimestamp(self._ldap2unix(self._GetSize(ret[self._COLUMN2PRINT["ModifyDT"]]))))
      if self._GetSize(ret[self._COLUMN2PRINT["AccessDT"]]) == 0:
        event_data.AccessDT = str(0)
      else:
        event_data.AccessDT = str(dt.utcfromtimestamp(self._ldap2unix(self._GetSize(ret[self._COLUMN2PRINT["AccessDT"]]))))
      if ret[self._COLUMN2PRINT["SUMMARY"]] is not None:
        event_data.SUMMARY = ret[self._COLUMN2PRINT["SUMMARY"]].encode('utf-8')
      else:
        event_data.SUMMARY = 'None'
      if ret[self._COLUMN2PRINT["Title"]] is not None:
        event_data.Title = ret[self._COLUMN2PRINT["Title"]].encode('utf-8')
      else:
        event_data.Title = 'None'
      if ret[self._COLUMN2PRINT["Subject"]] is not None:
        event_data.Subject = ret[self._COLUMN2PRINT["Subject"]].encode('utf-8')
      else:
        event_data.Subject = 'None'
      if ret[self._COLUMN2PRINT["Comment"]] is not None:
        event_data.Comment = ret[self._COLUMN2PRINT["Comment"]].encode('utf-8')
      else:
        event_data.Comment = 'None'
      if ret[self._COLUMN2PRINT["Label"]] is not None:
        event_data.Label = ret[self._COLUMN2PRINT["Label"]].encode('utf-8')
      else:
        event_data.Label = 'None'
      if ret[self._COLUMN2PRINT["Text"]] is not None:
        event_data.Text = ret[self._COLUMN2PRINT["Text"]].encode('utf-8')
      else:
        event_data.Text = 'None'
      if ret[self._COLUMN2PRINT["APPName"]] is not None:
        event_data.APPName = ret[self._COLUMN2PRINT["APPName"]].encode('utf-8')
      else:
        event_data.APPName = 'None'

      if self._GetSize(ret[self._COLUMN2PRINT["CreateDT"]]) == 0:
        date_time = dfdatetime_semantic.SemanticTime('Not set')
        desc = definitions.TIME_DESCRIPTION_NOT_A_TIME
      else:
        createDT = self._GetSize(ret[self._COLUMN2PRINT["CreateDT"]])
        date_time = dfdatetime_filetime.Filetime(timestamp=int(createDT))
        desc = definitions.TIME_DESCRIPTION_CREATION

      event = time_events.DateTimeValuesEvent(date_time, desc)
      parser_mediator.ProduceEventWithEventData(event, event_data)


esedb.ESEDBParser.RegisterPlugin(WinSearchESEDBPlugin)
