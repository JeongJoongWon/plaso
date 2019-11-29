# -*- coding: utf-8 -*-
"""The Windows installation event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsRegistryInstallationEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Windows installation event."""

  DATA_TYPE = 'windows:registry:installation'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Systemroot : {path}',
      'Productname : {product_name}',
      'CurrentVersion : {version}',
      'BuildLabEx : {buildLab}',
      'ProductId : {product_id}',
      'Owner: {owner}',
      'InstallDate: {date}',
      'InstallTime: {time}',
      'Origin: {key_path}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{key_path}]',
      'Systemroot : {path}',
      'Productname : {product_name}',
      'CurrentVersion : {version}',
      'BuildLabEx : {buildLab}',
      'ProductId : {product_id}',
      'Owner: {owner}',
      'InstallDate: {date}',
      'InstallTime: {time}',
      'Origin: {key_path}']

  SOURCE_LONG = 'Registry Key: windows installation'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(
    WindowsRegistryInstallationEventFormatter)
