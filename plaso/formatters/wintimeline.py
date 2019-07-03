# -*- coding: utf-8 -*-
"""The Windows Timeline event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class WindowsTimelineActivityEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for generic Windows Timeline events."""

  DATA_TYPE = 'windows:timeline:activity'

  FORMAT_STRING_PIECES = [
      'Timeline Data: {timeline_data}'
  ]

  SOURCE_LONG = 'Windows Timeline - Activity'
  SOURCE_SHORT = 'Windows Timeline'

class WindowsTimelineActivityOperationEventFormatter(interface.ConditionalEventFormatter):
    """Formatter for activityoperation Windows Timeline database rows"""

    DATA_TYPE =  'windows:timeline:activityoperation'

    FORMAT_STRING_PIECES = [
        'Timeline Data: {timeline_data}'
    ]

    SOURCE_LONG = 'Windows Timeline - ActivityOperation'
    SOURCE_SHORT = 'windows Timeline'

class WindowsTimelineActivityPackageIdEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for generic Windows Timeline events."""

  DATA_TYPE = 'windows:timeline:activitypackageid'

  FORMAT_STRING_PIECES = [
      'Timeline Data: {timeline_data}'
  ]

  SOURCE_LONG = 'Windows Timeline - Activity PackageID'
  SOURCE_SHORT = 'Windows Timeline'

manager.FormattersManager.RegisterFormatters([
    WindowsTimelineActivityPackageIdEventFormatter, WindowsTimelineActivityOperationEventFormatter, WindowsTimelineActivityEventFormatter])
