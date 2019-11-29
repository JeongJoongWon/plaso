# -*- coding: utf-8 -*-
"""This file contains the externel storage list plugins for Plaso."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface

class ExternelStorageListEventData(events.EventData):
    """Externel Storage List Extract

    Attributes:
      #dd
      #
    """

    DATA_TYPE = 'windows:registry:externelstoragelist'

    def __init__(self):
        """Initializes event data."""
        super(ExternelStorageListEventData, self).__init__(data_type=self.DATA_TYPE)
        self.keypath = None
        self.device_name = None
        self.serial_number = None
        self.type = None
        self.product = None
        self.vendor = None
        self.first_connect_time = None
        self.first_disconnect_time = None
        self.first_connect_time_after_last_boot = None
        self.first_disconnect_time_after_last_boot = None
        self.last_connect_time = None


class ExternelStorageListPlugin(interface.WindowsRegistryPlugin):
    NAME = 'externelstoragelist'
    DESCRIPTION = 'Parser for Externel Storage List Registry data.'

    FILTERS = frozenset([
        interface.WindowsRegistryKeyPathFilter(
            'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MountPoints2'),
        interface.WindowsRegistryKeyPathFilter('HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum\\USBSTOR'),
        interface.WindowsRegistryKeyPathFilter('HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Enum\\USB')
    ])

    def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
        """Extracts events from a Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfvfs.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        if registry_key.name == 'USBSTOR':
            keypath = None
            device_name = None
            serial_number = None
            type = 'USBSTOR'
            product = None
            vendor = None
            first_connect_time = None
            first_disconnect_time = None
            first_connect_time_after_last_boot = None
            first_disconnect_time_after_last_boot = None
            last_connect_time = None
            for subkey in registry_key.GetSubkeys():
                subkey_name = subkey.name
                # subkey structure example : DISK&Ven_iptime&Prod_External&Rev_0309

                name_values = subkey_name.split('&')
                number_of_name_values = len(name_values)
                if number_of_name_values != 4:
                    logger.warning('Expected 4 &-separated values in: {0:s}'.format(subkey_name))

                if number_of_name_values >= 1:
                    type = name_values[0]
                if number_of_name_values >= 2:
                    vendor = name_values[1]
                if number_of_name_values >= 3:
                    product = name_values[2]

                for devicekey in subkey.GetSubkeys():
                    serial_number = devicekey.name

                    friendly_name_value = devicekey.GetValueByName('FriendlyName')
                    if friendly_name_value:
                        device_name = friendly_name_value.GetDataAsObject()

                    for subkey2 in devicekey.GetSubkeys():
                        # Device Parametes, Properties
                        if subkey2.name == "Properties":
                            for subkey3 in subkey2.GetSubkeys():
                                # {80497100-8c73-48b9-aad9-ce387e19c56e}
                                # {540b947e-8b40-45bc-a8a2-6a0b894cbda2} etc
                                if subkey3.name == '{83da6326-97a6-4088-9453-a1923f573b29}':
                                    temp_first_disconnect_time = time_events.DateTimeValuesEvent(
                                        subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
                                    first_disconnect_time = temp_first_disconnect_time.timestamp
                                    for detailkey in subkey3.GetSubkeys():
                                        # 0003 -> first_connect_time(Key modified time)
                                        # 0066 -> first_connect_time_after_last_boot(Key Modified time)
                                        # 0067 -> first_disconnect_time_after_last_boot(Key Modified time)
                                        if detailkey.name == '0003':
                                            temp_first_connect_time = time_events.DateTimeValuesEvent(
                                                subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
                                            first_connect_time = temp_first_connect_time.timestamp
                                        if detailkey.name == '0066':
                                            temp_first_connect_time_after_last_boot = time_events.DateTimeValuesEvent(
                                                subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
                                            first_connect_time_after_last_boot = temp_first_connect_time_after_last_boot.timestamp
                                        elif detailkey.name == '0067':
                                            temp_first_disconnect_time_after_last_boot = time_events.DateTimeValuesEvent(
                                                subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
                                            first_disconnect_time_after_last_boot = temp_first_disconnect_time_after_last_boot.timestamp

                    event_data = ExternelStorageListEventData()
                    event_data.key_path = registry_key.path
                    event_data.device_name = device_name
                    event_data.serial_number = serial_number
                    event_data.type = type
                    event_data.first_connect_time = first_connect_time
                    event_data.first_disconnect_time = first_disconnect_time
                    event_data.first_connect_time_after_last_boot = first_connect_time_after_last_boot
                    event_data.first_disconnect_time_after_last_boot = first_disconnect_time_after_last_boot
                    event_data.last_connect_time = last_connect_time
                    event = time_events.DateTimeValuesEvent(subkey.last_written_time,
                                                            definitions.TIME_DESCRIPTION_WRITTEN)
                    parser_mediator.ProduceEventWithEventData(event, event_data)

        elif registry_key.name == "MountPoints2":
            keypath = None
            device_name = None
            serial_number = None
            type = None
            product = None
            vendor = None
            first_connect_time = None
            first_disconnect_time = None
            first_connect_time_after_last_boot = None
            first_disconnect_time_after_last_boot = None
            last_connect_time = None
            for subkey in registry_key.GetSubkeys():
                name = subkey.name
                if not name:
                    continue

                device_name = name
                type = 'Drive'

                if name.startswith('{'):
                    device_name = name
                    type = 'Volume'
                    temp_last_connect_time = time_events.DateTimeValuesEvent(subkey.last_written_time,
                                                                             definitions.TIME_DESCRIPTION_WRITTEN)
                    last_connect_time = temp_last_connect_time.timestamp

                elif name.startswith('##'):
                    device_name = name
                    type = 'Remote Drive'
                    temp_last_connect_time = time_events.DateTimeValuesEvent(subkey.last_written_time,
                                                                             definitions.TIME_DESCRIPTION_WRITTEN)
                    last_connect_time = temp_last_connect_time.timestamp

                event_data = ExternelStorageListEventData()
                event_data.key_path = registry_key.path
                event_data.device_name = device_name
                event_data.serial_number = serial_number
                event_data.type = type
                event_data.first_connect_time = first_connect_time
                event_data.first_disconnect_time = first_disconnect_time
                event_data.first_connect_time_after_last_boot = first_connect_time_after_last_boot
                event_data.first_disconnect_time_after_last_boot = first_disconnect_time_after_last_boot
                event_data.last_connect_time = last_connect_time
                event = time_events.DateTimeValuesEvent(subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
                parser_mediator.ProduceEventWithEventData(event, event_data)

        elif registry_key.name == "USB":
            keypath = None
            device_name = None
            serial_number = None
            type = 'USB'
            product = None
            vendor = None
            first_connect_time = None
            first_disconnect_time = None
            first_connect_time_after_last_boot = None
            first_disconnect_time_after_last_boot = None
            last_connect_time = None

            for subkey in registry_key.GetSubkeys():
                # serial key
                for devicekey in subkey.GetSubkeys():
                    serial_number = devicekey.name
                    # devicename
                    _device_name = devicekey.GetValueByName('DeviceDesc')
                    temp_device_name = _device_name.data.decode('utf-8').replace('\x00', '')
                    device_name_parts = temp_device_name.split(';')
                    device_name = device_name_parts[1]
                    # timestamp
                    for subkey2 in devicekey.GetSubkeys():
                        # Device Parametes, Properties
                        if subkey2.name == "Properties":
                            for subkey3 in subkey2.GetSubkeys():
                                # {80497100-8c73-48b9-aad9-ce387e19c56e}
                                # {540b947e-8b40-45bc-a8a2-6a0b894cbda2} etc
                                if subkey3.name == '{83da6326-97a6-4088-9453-a1923f573b29}':
                                    temp_first_disconnect_time = time_events.DateTimeValuesEvent(
                                        subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
                                    first_disconnect_time = temp_first_disconnect_time.timestamp
                                    for detailkey in subkey3.GetSubkeys():
                                        # 0003 -> first_connect_time(Key modified time)
                                        # 0066 -> first_connect_time_after_last_boot(Key Modified time)
                                        # 0067 -> first_disconnect_time_after_last_boot(Key Modified time)
                                        if detailkey.name == '0003':
                                            temp_first_connect_time = time_events.DateTimeValuesEvent(
                                                subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
                                            first_connect_time = temp_first_connect_time.timestamp
                                        elif detailkey.name == '0066':
                                            temp_first_connect_time_after_last_boot = time_events.DateTimeValuesEvent(
                                                subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
                                            first_connect_time_after_last_boot = temp_first_connect_time_after_last_boot.timestamp
                                        elif detailkey.name == '0067':
                                            temp_first_disconnect_time_after_last_boot = time_events.DateTimeValuesEvent(
                                                subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
                                            first_disconnect_time_after_last_boot = temp_first_disconnect_time_after_last_boot.timestamp

                    subkey_name_parts = subkey.name.split('&')
                    if len(subkey_name_parts) >= 2:
                        identification_vendor = subkey_name_parts[0]
                        identification_product = subkey_name_parts[1]
                        if identification_vendor and identification_product:
                            vendor = identification_vendor
                            product = identification_product

                    event_data = ExternelStorageListEventData()
                    event_data.key_path = registry_key.path
                    event_data.device_name = device_name
                    event_data.serial_number = serial_number
                    event_data.type = type
                    event_data.first_connect_time = first_connect_time
                    event_data.first_disconnect_time = first_disconnect_time
                    event_data.first_connect_time_after_last_boot = first_connect_time_after_last_boot
                    event_data.first_disconnect_time_after_last_boot = first_disconnect_time_after_last_boot
                    event_data.last_connect_time = last_connect_time
                    event = time_events.DateTimeValuesEvent(subkey.last_written_time,
                                                            definitions.TIME_DESCRIPTION_WRITTEN)
                    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(ExternelStorageListPlugin)
