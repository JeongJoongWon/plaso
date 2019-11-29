# -*- coding: utf-8 -*-
"""The BagMRU event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ExternalStorageListFormatter(interface.ConditionalEventFormatter):
  """Formatter for a ExternalStorageList event."""

  DATA_TYPE = 'windows:registry:externelstoragelist'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Device Name: {device_name}',
      'Serial Number: {serial_number}',
      'Type: {type}',
      'Product: {product}',
      'Vendor: {vendor}',
      'first_connect_time:{first_connect_time}',
      'first_disconnect_time : {first_disconnect_time}',
      'first_connect_time_after_last_boot : {first_connect_time_after_last_boot}',
      'first_disconnect_time_after_last_boot : {first_disconnect_time_after_last_boot}',
      'last_connect_time : {last_connect_time}'
  ]
  SOURCE_LONG = 'Externel Storage List'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(ExternalStorageListFormatter)
