# -*- coding: utf-8 -*-
"""The Windows Superfetch event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class WindowsSuperfetchFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Superfetch event."""

  DATA_TYPE = 'windows:superfetch:execution'

  FORMAT_STRING_PIECES = [
      'FILE INFO: {file_info}',
      'SUPERFETCH INFO:  {superfetch_info}'
      ]

  SOURCE_LONG = 'WinSuperfetch'
  SOURCE_SHORT = 'LOG'

  def GetMessages(self, formatter_mediator, event):
      event_values = event.CopyToDict()
      event_values['file_info'] = event_values.get('file_info', None)
      event_values['superfetch_info'] = event_values.get('superfetch_info', None)
      return self._ConditionalFormatMessages(event_values)

manager.FormattersManager.RegisterFormatter(WindowsSuperfetchFormatter)
