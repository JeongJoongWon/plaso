# -*- coding: utf-8 -*-
"""The Windows Search DB event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

import sys

'''class WindowsSearchdbFormatter(interface.ConditionalEventFormatter):'''
class WindowsSearchdbFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Search DB event."""

  DATA_TYPE = 'windows:searchdb:execution'

  FORMAT_STRING_PIECES = [
      'ID: {ID}',
      'Name: {Name}',
      'IType: {IType}',
      'Owner: {Owner}',
      'IURL: {IURL}',
      'IAttr: {IAttr}',
      'IsFolder: {IsFolder}',
      'Size: {Size}',
      'GatherDT: {GatherDT}',
      'CreateDT: {CreateDT}',
      'ModifyDT: {ModifyDT}',
      'AccessDT: {AccessDT}',
      'SUMMARY: {SUMMARY}',
      'Title: {Title}',
      'Subject: {Subject}',
      'Comment: {Comment}',
      'Label: {Label}',
      'Text: {Text}',
      'APPName: {APPName}',

      ]

  SOURCE_LONG = 'WinSearchDB'
  SOURCE_SHORT = 'LOG'

  FORMAT_LIST = ['ID', 'Name', 'IType', 'Owner', 'IURL', 'IAttr', 'IsFolder', 'Size', 'GatherDT', 'CreateDT', 'ModifyDT', 'AccessDT', 'SUMMARY', 'Title', 'Subject', 'Comment', 'Label', 'Text', 'APPName']

  def GetMessages(self, formatter_mediator, event):
      event_values = event.CopyToDict()
      for key in self.FORMAT_LIST:
        ret = event_values.get(key, None)
        event_values[key] = ret
      return self._ConditionalFormatMessages(event_values)

manager.FormattersManager.RegisterFormatter(WindowsSearchdbFormatter)
