# -*- coding: utf-8 -*-
"""Parser for Windows WinSearchDB files."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager

import time
import os
import sys
from datetime import datetime as dt
import pyesedb as edb

reload(sys)
sys.setdefaultencoding('utf8')

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
    self.IType = None
    self.Owner = None
    self.IURL = None
    self.IAttr = None
    self.IsFolder = None
    self.Size = None
    self.GatherDT = None
    self.CreateDT = None
    self.ModifyDT = None
    self.AccessDT = None
    self.SUMMARY = None
    self.Title = None
    self.Subject = None
    self.Comment = None
    self.Label = None
    self.Text = None
    self.APPName = None
    '''
      Attributes:
    '''

class WinSearchDBParser(interface.FileObjectParser):
  """A parser for Windows Search DB files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'winsearchdb'
  DESCRIPTION = 'Parser for Windows SearchDB files.'

  HEX_MAP = {"0":0, "1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7, "8":8, "9":9, "a":10, "b":11, "c":12, "d":13, "e":14, "f":15}
  # = {9:"Binary Data", 1:"Boolean", 5:"Currency", 8:"Datetime", 7:"Double 64bit", 6:"Float 32bit", 16:"GUID", 3:"Int 16bit signed", 17:"Int 16bit unsigned", 4:"Int 32bit signed", 14:"Int 32bit unsigned", 15:"Int 64bit signed", 2:"Int 8bit unsigned", 11:"Large Binary Data", 12:"Large Text", 0:"NULL", 13:"Super Large Value", 10:"Text"}
  
  INT_TYPES = [3, 17, 4, 14, 15, 2]
  REAL_TYPES = [7, 6]
  STRING_TYPES = [12, 10]
  BINARY_TYPES = [9, 11]
  TYPES=[5, 8, 0, 13, 16]
  TARGET_COLUMNS = ['WorkID', 'System_FileName', 'System_ItemTypeText', 'System_FileOwner', 'System_ItemUrl', 'System_FileAttributes', 'System_IsFolder', 'System_Size', 'System_Search_GatherTime', 'System_DateCreated', 'System_DateModified', 'System_DateAccessed', 'System_Search_AutoSummary', 'System_Title', 'System_Subject', 'System_Comment', 'System_Contact_Label', 'System_PriorityText', 'System_ApplicationName']
  COLUMN2PRINT = {"ID":"WorkID", "Name":"System_FileName", "IType":"System_ItemTypeText", "Owner":"System_FileOwner", "IURL":"System_ItemUrl", "IAttr":"System_FileAttributes", "IsFolder":"System_IsFolder", "Size":"System_Size", "GatherDT":"System_Search_GatherTime", "CreateDT":"System_DateCreated", "ModifyDT":"System_DateModified", "AccessDT":"System_DateAccessed", "SUMMARY":"System_Search_AutoSummary", "Title":"System_Title", "Subject":"System_Subject", "Comment":"System_Comment", "Label":"System_Contact_Label", "Text":"System_PriorityText", "APPName":"System_ApplicationName" }
  
  def unix2ldap(self, unix):
    converter = ((1970 - 1601) * 365 - 3 + round((1970 - 1601) / 4)) * 86400
    epoch = round(converter + unix)
    return epoch * 10000000

  def ldap2unix(self, ldap):
    uSecs = ldap/10000000
    uTimestamp = uSecs - 11644473600
    return uTimestamp
  
  def GetSize(self, bData):
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

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'\x02\xE9\xC7\x43\xEF\xCD\xAB\x89', offset=0)
    return format_specification

  def ParseRecords(self):
    fn = open('tmp_ijb_win.db', 'rb')
    edb_file = edb.file()
    edb_file.open_file_object(fn)
    win_ret = []
    for tb in edb_file.tables:
      if tb.name == 'SystemIndex_PropertyStore' or tb.name == 'SystemIndex_0A':
        for row in range(0, tb.get_number_of_records()):
          r = tb.get_record(row)
          r_val = r.get_number_of_values()
          cmn_ret = {"WorkID":"", "System_FileName":"", "System_ItemTypeText":"", "System_FileOwner":"", "System_ItemUrl":"", "System_FileAttributes":"", "System_IsFolder":"", "System_Size":"", "System_Search_GatherTime":"", "System_DateCreated":"", "System_DateModified":"", "System_DateAccessed":"", "System_Search_AutoSummary":"", "System_Title":"", "System_Subject":"", "System_Comment":"", "System_Contact_Label":"", "System_PriorityText":"", "System_ApplicationName":"" }
          for rv in range(0, r_val):
            for n in self.TARGET_COLUMNS:
              cmn = r.get_column_name(rv)
              cmn = cmn[len(n)*-1:]
              if n in cmn[len(n)*-1:]:
                cmn_type = r.get_column_type(rv)
                if cmn_type in self.INT_TYPES:
                  cmn_ret[cmn] = str(r.get_value_data_as_integer(rv))
                elif cmn_type in self.STRING_TYPES:
                  ret = r.get_value_data_as_string(rv)
                  if ret is not None:
                    cmn_ret[cmn] = ret.encode('utf-8')
                  else:
                    cmn_ret[cmn] = "None"
                elif cmn_type in self.BINARY_TYPES:
                  if cmn[len(n)*-1:] == 'System_Size':
                    cmn_ret[cmn] = str(self.GetSize(r.get_value_data(rv)))
                  else:
                    tm = self.GetSize(r.get_value_data(rv))
                    if tm == 0:
                      cmn_ret[cmn] = str(0)
                    else:
                      cmn_ret[cmn] = str(dt.utcfromtimestamp(self.ldap2unix(tm)))
                elif cmn_type in self.TYPES:
                  cmn_ret[cmn] = str(r.get_value_data(rv))
                elif cmn_type in self.REAL_TYPES:
                  cmn_ret[cmn] = str(r.get_value_data_as_floating_point(rv))
                elif cmn_type == 1:
                  cmn_ret[cmn] = str(r.get_value_data_flags(rv))
          win_ret.append(cmn_ret)

    edb_file.close()
    fn.close()
    os.remove('tmp_ijb_win.db')
    return win_ret

  def saveFile(self, file_object):
    #file_len = file_object.get_size()
    current_offset = file_object.get_offset()
    file_object.seek(0)
    file_data = file_object.read()
    f=open('tmp_ijb_win.db', 'wb')
    f.write(file_data)
    f.close()
    file_object.seek(current_offset)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Windows Search DB file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """

    self.saveFile(file_object)
    win_ret = self.ParseRecords()
    for ret in win_ret:
      event_data = WinSearchDBExecutionEventData()
      event_data.ID = ret[self.COLUMN2PRINT["ID"]]
      event_data.Name = ret[self.COLUMN2PRINT["Name"]]
      event_data.IType = ret[self.COLUMN2PRINT["IType"]]
      event_data.Owner = ret[self.COLUMN2PRINT["Owner"]]
      event_data.IURL = ret[self.COLUMN2PRINT["IURL"]]
      event_data.IAttr = ret[self.COLUMN2PRINT["IAttr"]]
      event_data.IsFolder = ret[self.COLUMN2PRINT["IsFolder"]]
      event_data.Size = ret[self.COLUMN2PRINT["Size"]]
      event_data.GatherDT = ret[self.COLUMN2PRINT["GatherDT"]]
      event_data.CreateDT = ret[self.COLUMN2PRINT["CreateDT"]]
      event_data.ModifyDT = ret[self.COLUMN2PRINT["ModifyDT"]]
      event_data.AccessDT = ret[self.COLUMN2PRINT["AccessDT"]]
      event_data.SUMMARY = ret[self.COLUMN2PRINT["SUMMARY"]]
      event_data.Title = ret[self.COLUMN2PRINT["Title"]]
      event_data.Subject = ret[self.COLUMN2PRINT["Subject"]]
      event_data.Comment = ret[self.COLUMN2PRINT["Comment"]]
      event_data.Label = ret[self.COLUMN2PRINT["Label"]]
      event_data.Text = ret[self.COLUMN2PRINT["Text"]]
      event_data.APPName = ret[self.COLUMN2PRINT["APPName"]]

      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      desc = definitions.TIME_DESCRIPTION_NOT_A_TIME

      event = time_events.DateTimeValuesEvent(date_time, desc)
      parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(WinSearchDBParser)
