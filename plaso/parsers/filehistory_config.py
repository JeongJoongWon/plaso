# -*- coding: utf-8 -*-
"""Parser for the FileHistory Config.xml files."""

from __future__ import unicode_literals

import os

from defusedxml import ElementTree
from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager

class FileHistoryConfigEventData(events.EventData):
    """Windows FileHistory event data.

    Attributes:
        user_name (str)
        friendly_name (str)
        pc_name (str)
        library (str)
        user_folder (str)
        folder_exclude (str)
        retention_policy (str)
        minimum_retention_age (str)
        dp_frequency (str)
        dp_status (str)
        target_name (str)
        target_url (str)
        target_volume_path (str)
        target_backup_store_path (str)
    """

    DATA_TYPE = 'filehistory:config:event'

    def __init__(self):
        """Initializes event data."""
        super(FileHistoryConfigEventData, self).__init__(data_type=self.DATA_TYPE)
        self.user_name = ''
        self.friendly_name = ''
        self.pc_name = ''
        self.library = ''
        self.user_folder = ''
        self.folder_exclude = ''
        self.retention_policy = ''
        self.minimum_retention_age = ''
        self.dp_frequency = ''
        self.dp_status = ''
        self.target_name = ''
        self.target_url = ''
        self.target_volume_path = ''
        self.target_backup_store_path = ''

class FileHistoryConfigParser(interface.FileObjectParser):
    """Parses an Windows FileHistory Config.xml file-like object"""

    NAME = 'filehistory_config'
    DESCRIPTION = 'Parser for Windows filehistory Config.xml files.'

    _HEADER_READ_SIZE = 128

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses an Windows FileHistory Config file-like object.

        Args:
            parser_mediator (ParserMediator): mediates interactions between parsers
                and other components, such as storage and dfvfs.
            file_object (dfvfs.FileIO): file-like object.

        Raises:
            unableToParseFile: when the file cannot be parsed.
        """
        data = file_object.read(self._HEADER_READ_SIZE)
        if not data.startswith(b'<?xml'):
            raise errors.UnableToParseFile(
                'Not an Windows FileHistory Config.xml file [not XML]')

        _, _, data = data.partition(b'\n')
        if not data.startswith(b'<DataProtectionUserConfig'):
            raise errors.UnableToParseFile(
                'Not an Windows FileHistory Config.xml file [wrong XML root key]')

        # the current offset of the file-like object needs to point at
        # the start of the file for ElementTree to parse the XML data correctly.
        file_object.seek(0, os.SEEK_SET)

        xml = ElementTree.parse(file_object)
        root_node = xml.getroot()
        event_data = FileHistoryConfigEventData()

        for sub_node in root_node:
            str_tag = sub_node.tag
            if str_tag == 'UserName':
                event_data.user_name = sub_node.text
                continue
            if str_tag == 'FriendlyName':
                event_data.friendly_name = sub_node.text
                continue
            if str_tag == 'PCName':
                event_data.pc_name = sub_node.text
                continue
            if str_tag == 'Library':
                for sub_lib_node in sub_node:
                    str_sub_tag = sub_lib_node.tag
                    if str_sub_tag == 'Folder':
                        event_data.library += sub_lib_node.text + ", "
                        continue
                    else:
                        continue
            if str_tag == 'UserFolder':
                event_data.user_folder += sub_node.text + ", "
                continue
            if 'FolderExclude' in str_tag:
                event_data.folder_exclude += sub_node.text + ", "
                continue
            if str_tag == 'RetentionPolicies':
                for sub_ret_node in sub_node:
                    str_sub_tag = sub_ret_node.tag
                    if str_sub_tag == 'RetentionPolicyType':
                        if sub_ret_node.text == 'DISABLED':
                            event_data.retention_policy = "Forever Retention"
                            continue
                        if sub_ret_node.text == 'AGE LIMIT':
                            event_data.retention_policy = "Limited Retention"
                            continue
                        if sub_ret_node.text == 'NO LIMIT':
                            event_data.retention_policy = "Until Space is Needed"
                            continue
                        else:
                            event_data.retention_policy = sub_ret_node.text
                    if str_sub_tag == 'MinimumRetentionAge':
                        if sub_ret_node.text == '1':
                            event_data.minimum_retention_age = "1 Month"
                            continue
                        if sub_ret_node.text == '3':
                            event_data.minimum_retention_age = "3 Month"
                            continue
                        if sub_ret_node.text == '6':
                            event_data.minimum_retention_age = "6 Month"
                            continue
                        if sub_ret_node.text == '9':
                            event_data.minimum_retention_age = "9 Month"
                            continue
                        if sub_ret_node.text == '12':
                            event_data.minimum_retention_age = "1 Year"
                            continue
                        if sub_ret_node.text == '24':
                            event_data.minimum_retention_age = "2 Year"
                            continue
                        else:
                            event_data.minimum_retention_age = sub_ret_node.text
                            continue
            if str_tag == 'DPFrequency':
                event_data.dp_frequency = sub_node.text + ' second'
                continue
            if str_tag == 'DPStatus':
                event_data.dp_status = sub_node.text
                continue
            if str_tag == 'Target':
                for sub_target_node in sub_node:
                    str_sub_tag = sub_target_node.tag
                    if str_sub_tag == 'TargetName':
                        event_data.target_name = sub_target_node.text
                        continue
                    if str_sub_tag == 'TargetUrl':
                        event_data.target_url = sub_target_node.text
                        continue
                    if str_sub_tag == 'TargetVolumePath':
                        event_data.target_volume_path = sub_target_node.text
                        continue
                    if str_sub_tag == 'TargetBackupStorePath':
                        event_data.target_backup_store_path = sub_target_node.text
                        continue
                    else:
                        continue
            else:
                continue

        date_time = dfdatetime_java_time.JavaTime(timestamp=0)
        event = time_events.DateTimeValuesEvent(
            date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
        parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(FileHistoryConfigParser)