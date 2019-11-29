# -*- coding: utf-8 -*-
"""The Windows FileHistory Config.xml event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class FileHistoryConfigFormatter(interface.ConditionalEventFormatter):
    """Formatter for an Windows FileHistory Config parsing result."""

    DATA_TYPE = 'filehistory:config:event'

    FORMAT_STRING_PIECES = [
        'UserName: {user_name}',
        'FriendlyName: {friendly_name}',
        'PCName: {pc_name}',
        'Library: {library}',
        'UserFolder: {user_folder}',
        'FolderExclude: {folder_exclude}',
        'RetentionPolicy: {retention_policy}',
        'RetentionAge: {minimum_retention_age}',
        'FileHistory Frequency: {dp_frequency}',
        'FileHistory Status: {dp_status}',
        'BackupStorage Name: {target_name}',
        'BackupStorage Drive Letter: {target_url}',
        'BackupStorage Volume GUID: {target_volume_path}',
        'BackupStorage Path: {target_backup_store_path}']

    SOURCE_LONG = 'FileHistory Configuration'
    SOURCE_SHORT = 'BACKUP'

manager.FormattersManager.RegisterFormatter(FileHistoryConfigFormatter)