# -*- coding: utf-8 -*-
"""The Windows Search DB event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

import sys

class WindowsSearchdbFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Search DB event."""

  DATA_TYPE = 'windows:searchdb:execution'

  FORMAT_STRING_PIECES = [
      'ID: {ID}',
      'Name: {Name}',
      'Owner: {Owner}',
      'IURL: {IURL}',
      'IAttr: {IAttr}',
      'IsFolder: {IsFolder}',
      'Size: {Size}',
      'GatherDT: {GatherDT}',
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

  FORMAT_LIST = ['ID', 'Name', 'Owner', 'IURL', 'IAttr', 'IsFolder', 'Size', 'GatherDT', 'CreateDT', 'ModifyDT', 'AccessDT', 'SUMMARY', 'Title', 'Subject', 'Comment', 'Label', 'Text', 'APPName']

manager.FormattersManager.RegisterFormatter(WindowsSearchdbFormatter)
