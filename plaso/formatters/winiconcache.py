# -*- coding: utf-8 -*-
"""The Windows Iconcache event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

'''class WindowsIconcacheFormatter(interface.ConditionalEventFormatter):'''
class WindowsIconcacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Iconcache event."""

  DATA_TYPE = 'windows:iconcache:execution'

  FORMAT_STRING_PIECES = [
      'Iconcache Info: {icon_info}'
      ]

  SOURCE_LONG = 'WinIconcache'
  SOURCE_SHORT = 'LOG'

  def GetMessages(self, formatter_mediator, event):
      event_values = event.CopyToDict()
      event_values['icon_info'] = event_values.get('icon_info', None)
      return self._ConditionalFormatMessages(event_values)

manager.FormattersManager.RegisterFormatter(WindowsIconcacheFormatter)
