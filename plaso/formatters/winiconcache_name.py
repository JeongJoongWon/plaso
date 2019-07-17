# -*- coding: utf-8 -*-
"""The Windows IconCache.db event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class WindowsIconcacheNameFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows IconCache.db Name."""

  DATA_TYPE = 'windows:iconcache:name:execution'

  FORMAT_STRING_PIECES = [
      'Iconcache Info: {icon_info}'
      ]

  SOURCE_LONG = 'WinIconCacheName'
  SOURCE_SHORT = 'LOG'

  def GetMessages(self, formatter_mediator, event):
      event_values = event.CopyToDict()
      event_values['icon_info'] = event_values.get('icon_info', None)
      return self._ConditionalFormatMessages(event_values)

manager.FormattersManager.RegisterFormatter(WindowsIconcacheNameFormatter)
