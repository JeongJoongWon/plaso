#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the airport plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers.plist_plugins import airport

from tests.parsers.plist_plugins import test_lib


class AirportPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the airport plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.airport.preferences.plist'

    plugin_object = airport.AirportPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 4)

    expected_timestamps = sorted([
        1375144166000000, 1386874984000000, 1386949546000000,
        1386950747000000])
    timestamps = sorted([
        event_object.timestamp for event_object in storage_writer.events])

    self.assertEqual(timestamps, expected_timestamps)

    event_object = storage_writer.events[0]
    self.assertEqual(event_object.key, u'item')
    self.assertEqual(event_object.root, u'/RememberedNetworks')

    expecte_description = (
        u'[WiFi] Connected to network: <europa> using security '
        u'WPA/WPA2 Personal')
    self.assertEqual(event_object.desc, expecte_description)

    expected_message = u'/RememberedNetworks/item {0:s}'.format(
        expecte_description)
    expected_message_short = u'{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
