# -*- coding: utf-8 -*-
"""Parser for Windows Iconcache files."""

from __future__ import unicode_literals

from dfdatetime import semantic_time as dfdatetime_semantic

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager

import os
import sys
import platform as pl

import hashlib
import base64

'''
reload(sys)
sys.setdefaultencoding('utf8')
'''

class WinIconcacheExecutionEventData(events.EventData):
  """Windows Iconcache event data.

  Attributes:
      icon_info (str): Combined string of data below
          icon number
          name
          resolution
          Data
          data sha1
  """

  DATA_TYPE = 'windows:iconcache:execution'

  def __init__(self):
    """Initializes event data."""
    super(WinIconcacheExecutionEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.icon_info = None

class WinIconcacheParser(interface.FileObjectParser):
  """A parser for Windows Iconcache files."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'iconcache'
  DESCRIPTION = 'Parser for Windows Iconcache files.'

  HEX_MAP = {'0':0, '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'a':10, 'b':11, 'c':12, 'd':13, 'e':14, 'f':15}

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'CMMM', offset=0)
    return format_specification

  def GetEntryOff(self, bData):
    off = 0
    for b in bData:
      if b != b'\x00':
        off += self.hex2int(b)
    return off

  def hex2int(self, b):
    cnt = 0
    for i in range(0x00, 0xff):
      if chr(i) == b:
        break
      cnt += 1
    return (cnt)

  def GetSize(self, bData):
    size = 0
    idx = 0
    for b in bData:
      if len(hex(self.hex2int(b))) == 4:
        tens = self.HEX_MAP[hex(self.hex2int(b))[3]]
        size += tens*(16**idx)
        idx += 1
        units = self.HEX_MAP[hex(self.hex2int(b))[2]]
        size += units*(16**idx)
        idx += 1
      else:
        units = self.HEX_MAP[hex(self.hex2int(b))[2]]
        size += units*(16**idx)
        idx += 1
    return size

  def GetName(self, bData):
    name = ''
    for b in bData:
      if b != b'\x00':
        name += str(self.hex2int(b))
    return name

  def GetSHA1(self, bData):
    h=hashlib.sha1()
    h.update(bData[82:])
    return h.hexdigest()

  def GetIconFormat(self, bData):
    fmat = ''
    for b in bData:
      fmat += str(self.hex2int(b))
    if fmat == "BM":
      return "BMP"
    else:
      return "PNG"

  def CheckEndData(self, bData):
    for b in bData:
      if b != b'\x00':
        return True
    return False

  def createFolder(self, dir):
    try:
      if not os.path.exists(dir):
        os.makedirs(dir)
    except OSError:
      print('Error: create directory. ' + dir)

  def ParseRecords(self, file_object):
    self.createFolder('winiconcache')
    icon_ret_split = []
    off = 0
    file_object.seek(0)

    off += 24
    bData = file_object.read(24)
    fEntry = bData[16:20]

    fEn = self.GetEntryOff(fEntry)
    if off == fEn:
      pass
    elif off < fEn:
      file_object.read(fEn-off)
      off = fEn
    elif off > fEn:
      pass

    bIdx = 1
    while True:
      off += 8
      bData = file_object.read(8)
      eSize = self.GetSize(bData[4:8])

      eData = file_object.read(32)
      if self.CheckEndData(eData) == False:
        break

      off += (eSize - 40)
      eData += file_object.read(eSize-40)
      iResX = self.GetSize(eData[20:24])
      iResY = self.GetSize(eData[24:28])
      iName = self.GetName(eData[48:80])
      iFmat = self.GetIconFormat(eData[82:84])
      iData = eData[82:]

      headBuf = bytes(iData[:2])
      if headBuf != b'BM':
        iData = b'BM' + eData[82:]

      if pl.system() == 'Linux': 
        fName = 'winiconcache//' + iName + '_' + self.GetSHA1(eData[82:])[:4] + '.jpg'
      else:
        fName = 'winiconcache\\' + iName + '_' + self.GetSHA1(eData[82:])[:4] + '.jpg'

      f=open(fName, 'wb')
      f.write(iData)
      f.close()

      icon_data = "iNo: " + str(bIdx) + " Name: " + iName + " ResXY: " + (str(iResX) + "x" + str(iResY)) + " ImgType: " + iFmat + " Data: " + str(base64.b64encode(iData)) + " SHA1: " + self.GetSHA1(eData[82:])
      icon_ret_split.append(icon_data)
      bIdx += 1

    return icon_ret_split

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Windows Iconcache file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    event_data = WinIconcacheExecutionEventData()
    date_time = dfdatetime_semantic.SemanticTime('Not set')

    icon_ret_split = self.ParseRecords(file_object)

    for ret in icon_ret_split:
      event_data.icon_info = ret
      event = time_events.DateTimeValuesEvent(date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)

manager.ParsersManager.RegisterParser(WinIconcacheParser)
