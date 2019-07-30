# -*- coding: utf-8 -*-
"""Parser for Windows Superfetch files."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager

import time
import os
import sys
import datetime as dt
import compressors as cm

#'''
reload(sys)
sys.setdefaultencoding('utf8')
#'''

class WinSuperfetchExecutionEventData(events.EventData):
  """Windows Superfetch event data.

  Attributes:
  """

  DATA_TYPE = 'windows:superfetch:execution'

  def __init__(self):
    """Initializes event data."""
    super(WinSuperfetchExecutionEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.file_info = None
    self.superfetch_info = None

class WinSuperfetchParser(interface.FileObjectParser):
  """A parser for Windows Superfetch files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'superfetch'
  DESCRIPTION = 'Parser for Windows Superfetch files.'
  HEX_MAP = {'0':0, '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'a':10, 'b':11, 'c':12, 'd':13, 'e':14, 'f':15}

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'MEM\x30', offset=0)
    return format_specification

  def unix2ldap(self, unix):
    converter = ((1970 - 1601) * 365 - 3 + round((1970 - 1601) / 4)) * 86400
    epoch = round(converter + unix)
    return epoch * 10000000

  def PrintStr2Timestamp(self, str):
    if len(str) > 19:
      date = str[0:10] + ' ' + str[-8:-1]
      timestamp = time.mktime(dt.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').timetuple())
      return timestamp
    else:
      return 0

  def hex2int(self, b):
    cnt = 0
    for i in range(0x00, 0xff):
      if chr(i) == b:
        break
      cnt += 1
    return (cnt)

  def GetSizeInt(self, nData):
    size = 0
    idx = 0
    for n in nData:
      if len(hex(n)) == 4:
        tens = self.HEX_MAP[hex(n)[3]]
        size += tens * (16**idx)
        idx += 1
        units = self.HEX_MAP[hex(n)[2]]
        size += units * (16**idx)
        idx += 1
      else:
        units = self.HEX_MAP[hex(n)[2]]
        size += units * (16**idx)
        idx += 2
    return size

  def ParseRecords(self, file_object):
    superfetch_info = {}
    file_info = [] 

    file_object.seek(0)
    input_data = file_object.read()

    len_unCompress = cm.GetSize(input_data[4:8])
    len_Compress = cm.GetSize(input_data[8:12])
    compress_data = input_data[12:len_Compress+12]
    
    out_buffer = bytearray(len_unCompress)
    ret = cm.XpressHuffman['OpenSrc'].Decompress(compress_data, out_buffer)

    out_buffer = out_buffer[244:]
    fName = ''
    for b in out_buffer:
      if 0 == b:
        break
      fName += chr(b)

    out_buffer = out_buffer[60:]
    timestamp = cm.ldap2unix(self.GetSizeInt(out_buffer[0:8]))
    volId = '0000%X%X-0000%X%X' % (out_buffer[11], out_buffer[10], out_buffer[9], out_buffer[8])
    dNmLen = self.GetSizeInt(out_buffer[20:22])

    out_buffer = out_buffer[32:]
    volName = ''
    for i in range(0, dNmLen*2):
      if out_buffer[i] != 0:
        volName += chr(out_buffer[i])

    superfetch_info['Name']=fName
    superfetch_info['Volumn Name'] = volName
    superfetch_info['Volumne ID'] = volId
    superfetch_info['Time'] = timestamp

    out_buffer = out_buffer[dNmLen*2:]
    bufSize = len(out_buffer)
    idx = 0
    cnt = 0
    while idx < bufSize:
      if out_buffer[idx] == 92 and out_buffer[idx+1] == 0 and out_buffer[idx+2] != 0 and out_buffer[idx+3] == 0:
        flen = self.GetSizeInt(out_buffer[idx-24:idx-20])/4
        if cm.chkFile(flen, out_buffer[idx:]) == False: 
          idx += 1
          continue
            
        fName=''
        for i in range(0, flen*2):
          if out_buffer[i+idx] != 0:
            fName += chr(out_buffer[i+idx])
        file_info.append(fName)
        idx += flen*2
        cnt += 1
      else:
        idx += 1

    return superfetch_info, file_info

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Superfetch file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    date_time = dfdatetime_filetime.Filetime(timestamp=int(time.time()))

    superfet_info, file_info = self.ParseRecords(file_object)
    super_ret =''

    for key in superfet_info.keys():
      super_ret += key + ":"
      if key == "Time":
        super_ret += str(dt.datetime.fromtimestamp(superfet_info[key])) + " " 
      else:
        super_ret += superfet_info[key] + " " 

    event_data = WinSuperfetchExecutionEventData()
    ldap_time = self.unix2ldap(superfet_info['Time'])
    date_time = dfdatetime_filetime.Filetime(timestamp=int(ldap_time))
    desc = definitions.TIME_DESCRIPTION_CREATION
    for ret in file_info:
      event_data.superfetch_info = super_ret
      event_data.file_info = ret
      event = time_events.DateTimeValuesEvent(date_time, desc)
      parser_mediator.ProduceEventWithEventData(event, event_data)

manager.ParsersManager.RegisterParser(WinSuperfetchParser)
