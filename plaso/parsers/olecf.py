# -*- coding: utf-8 -*-
"""Parser for OLE Compound Files (OLECF)."""

from __future__ import unicode_literals

import pyolecf

from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager

import os
import platform as pl

from dfdatetime import semantic_time as dfdatetime_semantic_time
from plaso.containers import time_events
from plaso.containers import events
from plaso.lib import definitions

import base64 as b64
import hashlib


class WinThumbnailExecutionEventData(events.EventData):
  """Windows Thumbnail event data.: IJB

  Attributes:
    thumbs_info (str): thumbnail image data (Base64 encoding)
    thumbs_sha1 (str): thumbnail image data SHA1
  """

  DATA_TYPE = 'windows:thumbnail:execution'

  def __init__(self):
    """Initializes event data."""
    super(WinThumbnailExecutionEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.thumbs_info = None
    self.thumbs_sha1 = None

class OLECFParser(interface.FileObjectParser):
  """Parses OLE Compound Files (OLECF)."""

  # pylint: disable=no-member

  _INITIAL_FILE_OFFSET = None

  NAME = 'olecf'
  DESCRIPTION = 'Parser for OLE Compound Files (OLECF).'

  IMG_DELIMITER = [24, 0, 0, 0, 3, 0, 0, 0]
  HEX_MAP = {"0":0, "1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7, "8":8, "9":9, "a":10, "b":11, "c":12, "d":13, "e":14, "f":15}

  _plugin_classes = {}

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)

    # OLECF
    format_specification.AddNewSignature(
        b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', offset=0)

    # OLECF beta
    format_specification.AddNewSignature(
        b'\x0e\x11\xfc\x0d\xd0\xcf\x11\x0e', offset=0)

    return format_specification

  def GetSHA1(self, bData):    
    h=hashlib.sha1()
    h.update(bData)
    return h.hexdigest()

  def OpenBF(self, file_name):
    fn = file_name
    fh = open(fn, 'rb')
    return fh

  def ReadB(self, fh, offset):
    ss = ''
    ss = fh.read(offset)
    return ss

  def ChkDelimiter(self, bData):
    idx = 0
    if not bData:
      return False
    for b in bData:
      if int(ord(b)) != self.IMG_DELIMITER[idx]:
        return False
      idx += 1
    return True

  def GetSize(self, bData):
    size = 0
    idx = 0
    for b in bData:
      if len(hex(ord(b))) == 4:
        tens = self.HEX_MAP[hex(ord(b))[3]]
        size += tens*(16**idx)
        idx += 1
        units = self.HEX_MAP[hex(ord(b))[2]]
        size += units*(16**idx)
        idx += 1
      else:
        units = self.HEX_MAP[hex(ord(b))[2]]
        size += units*(16**idx)
        idx += 2
    return size

  def GetJpgSize(self, bData):
    if self.ChkDelimiter(bData[-26:-18]) == True:
      return self.GetSize(bData[-18:-10])
    else:
      return self.GetSize(bData[-6:-2])

  def GetPngSize(self, bData):
    if self.ChkDelimiter(bData[-28:-20]) == True:
      return self.GetSize(bData[-20:-12])
    else:
      return self.GetSize(bData[-5:-9])

  def ChkHeaderPattern(self, bData):
    if ord(bData[79]) == 255 and ord(bData[78]) == 255 and ord(bData[77]) == 255 and ord(bData[76]) == 255 and ord(bData[127]) == 0 and ord(bData[126]) == 0 and ord(bData[125]) == 0 and ord(bData[124]) == 0 and ord(bData[207]) == 255 and ord(bData[206]) == 255 and ord(bData[205]) == 255 and ord(bData[204]) == 255 and ord(bData[255]) == 0 and ord(bData[254]) == 0 and ord(bData[253]) == 0 and ord(bData[252]) == 0:
      return True
    return False

  def ChkFFPattern(self, bData):
    for b in bData:
      if ord(b) != 255:
        return False
    return True
  
  def ChkFFPattern2(self, bData):
    if 255 == ord(bData[-1]) == ord(bData[-2]) == ord(bData[-3]) ==ord(bData[-4]) ==ord(bData[-5]) ==ord(bData[-6]) ==ord(bData[-7]) ==ord(bData[-8]) ==ord(bData[-9]) ==ord(bData[-10]) ==ord(bData[-11]) ==ord(bData[-12]) ==ord(bData[-13]) ==ord(bData[-14]) ==ord(bData[-15]) and 254 ==ord(bData[-16]):
      return True
    return False
  
  def ChkZero(self, bData):
    for b in bData:
      if ord(b) != 0:
        return False
    return True

  def ChkHeader(self, bData):
    for i in range(0, 15):
      if ord(bData[i]) == 255 and ord(bData[i+1]) == 216:
        return True
    return False
  
  def ChkFooter(self, bData):
    for i in range(0, 15):
      if ord(bData[i]) == 255 and ord(bData[i+1]) == 217:
        if ord(bData[i+2]) == 0:
          return True
    return False
  
  def FindHeader(self, bData):
    data = []
    for i in range(0, 511):
      if ord(bData[i]) == 255 and ord(bData[i+1]) == 216: 
        data.append('jpg')
        data.append(self.GetJpgSize(bData[0:i+2]))
        data.append(i)
        return data
    for i in range(0, 508):
      if ord(bData[i]) == 137 and ord(bData[i+1]) == 80 and ord(bData[i+2]) == 78 and ord(bData[i+3]) == 71: 
        data.append('png')
        data.append(self.GetPngSize(bData[0:i+4]))
        data.append(i)
        return data
  
  def FindFooter(self, bData):
    if ord(bData[-2]) == 255 and ord(bData[-1]) == 217: 
        return True
    if ord(bData[-4]) == 174 and ord(bData[-3]) == 66 and ord(bData[-2]) == 96 and ord(bData[-1]) == 130: 
        return True
    return False
  
  def GetNxtOff(self, cur):
    nxt = 0
    while True:
      if nxt > cur:
        return nxt
      nxt += 512
  
  def GetPreOff(self, cur):
    pre = self.GetNxtOff(cur) - 512
    while True:
      if pre > cur:
        return pre - 16
      pre += 16

  def createFolder(self, dir):
    try:
      if not os.path.exists(dir):
        os.makedirs(dir)
    except OSError:
      print("Error: create directory. " + dir)

  def IJBParserRecords(self, file_object):
    file_object.seek(0)

    off = 0
    imgOff = []
    imgType = []
    imgSize = []
    findF = -1
    while True:
      off += 512 
      nData = file_object.read(512)
      if not nData:
        break
    
      if self.ChkHeaderPattern(nData) == True:
        continue
      if self.ChkFFPattern(nData) == True:
        continue
    
      ret = self.FindHeader(nData)
      if not ret:
        pass
      elif ret[0] == 'jpg':
        findF += 1
        imgType.append(ret[0])
        imgSize.append(ret[1])
        imgOff.append((off + ret[2] - 512))
      elif ret[0] == 'png':
        findF += 1
        imgType.append(ret[0])
        imgSize.append(ret[1])
        imgOff.append((off + ret[2] - 512))

    if findF == -1:
      return "FAIL"

    file_object.seek(0)
    idx = 1
    thumb_ret = []
    for i in range(0, findF+1):
      file_object.seek(imgOff[i])
      fData = file_object.read(imgSize[i])
      if self.FindFooter(fData) == True:
        thumb_ret.append(str(b64.b64encode(fData)))
      else:
        while True:
          chkOff = self.GetNxtOff(imgOff[i])
          file_object.seek(chkOff)
          hData = file_object.read(512)
          if self.ChkHeaderPattern(hData) == True or self.ChkFFPattern(hData) == True or self.ChkFFPattern2(hData) == True:
            fData = fData[:chkOff-imgOff[i]]
            fData += file_object.read(imgSize[i]-(chkOff-imgOff[i]))
            if self.FindFooter(fData) == True:
              thumb_ret.append(str(b64.b64encode(fData)))
              break
    
          if (imgOff[i] + imgSize[i]) > imgOff[i+1]:
            remainSize = imgSize[i] + 12 - (imgOff[i+1] - imgOff[i])
            fData = fData[0:imgSize[i]-remainSize]
            file_object.seek(imgOff[i+1] + imgSize[i+1])
            for i in range(0,4):
              rData = file_object.read(16)
              while True:
                if self.ChkZero(rData) == True:
                  rData = file_object.read(16)
                else: break
            fData += file_object.read(remainSize)
            if self.FindFooter(fData) == True:
              thumb_ret.append(str(b64.b64encode(fData)))
              break
    
          chkOff = self.GetPreOff(imgOff[i])
          file_object.seek(chkOff)
          preC = -1
          while True:
            lData = file_object.read(16)
            if len(lData) < 16:
              break
    
            if self.ChkHeader(lData) == True:
              preC = 1
            if self.ChkFooter(lData) == True:
              if preC == 2:
                end_pos = 0
                for l in reversed(lData):
                  end_pos -= 1
                  if ord(l) == 217:
                    break
                lLen = 16+end_pos+1
                fData = fData[:(16+end_pos)*-1] + lData[:lLen]
                break
              preC = 2
            chkOff += 16
          if self.FindFooter(fData) == True:
            thumb_ret.append(str(b64.b64encode(fData)))
            break
      idx += 1

    return thumb_ret

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an OLE Compound File (OLECF) file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    ijb_ret = self.IJBParserRecords(file_object)
    if ijb_ret is not "FAIL":
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      i = 0
      for ret in ijb_ret:
        if ret:
          event_data = WinThumbnailExecutionEventData()
          event_data.thumbs_info = ret

          self.createFolder('winthumbnail')
          if pl.system() == 'Linux':
            fName = 'winthumbnail//' + str(i) + '_' + self.GetSHA1(ret)[:4] +  '.jpg'
          else:
            fName = 'winthumbnail\\' + str(i) + '_' + self.GetSHA1(ret)[:4] +  '.jpg'
          f=open(fName, 'wb')
          f.write(b64.b64decode(ret))
          f.close()
          i += 1

          event_data.thumbs_sha1 = self.GetSHA1(ret)
          event = time_events.DateTimeValuesEvent(date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
          parser_mediator.ProduceEventWithEventData(event, event_data)
      return
    else:
      olecf_file = pyolecf.file()
      olecf_file.set_ascii_codepage(parser_mediator.codepage)

      try:
        olecf_file.open_file_object(file_object)
      except IOError as exception:
        parser_mediator.ProduceExtractionError(
            'unable to open file with error: {0!s}'.format(exception))
        return

      root_item = olecf_file.root_item
      if not root_item:
        return

      # Get a list of all items in the root item from the OLECF file.
      item_names = [item.name for item in root_item.sub_items]

      # Compare the list of available plugin objects.
      # We will try to use every plugin against the file (except
      # the default plugin) and run it. Only if none of the plugins
      # works will we use the default plugin.

      item_names = frozenset(item_names)

      try:
        for plugin in self._plugins:
          if parser_mediator.abort:
            break

          if not plugin.REQUIRED_ITEMS.issubset(item_names):
            continue

          try:
            plugin.UpdateChainAndProcess(parser_mediator, root_item=root_item)

          except Exception as exception:  # pylint: disable=broad-except
            parser_mediator.ProduceExtractionError((
                'plugin: {0:s} unable to parse OLECF file with error: '
                '{1!s}').format(plugin.NAME, exception))

        if self._default_plugin and not parser_mediator.abort:
          try:
            self._default_plugin.UpdateChainAndProcess(
                parser_mediator, root_item=root_item)

          except Exception as exception:  # pylint: disable=broad-except
            parser_mediator.ProduceExtractionError((
                'plugin: {0:s} unable to parse OLECF file with error: '
                '{1!s}').format(self._default_plugin.NAME, exception))

      finally:
        olecf_file.close()


manager.ParsersManager.RegisterParser(OLECFParser)
