# -*- coding: utf-8 -*-
"""Parser for the Windows Timeline Database.

The Windows Timeline is stored in SQLite database files named History.db
"""
from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface

import sys
from dfdatetime import semantic_time as dfdatetime_semantic
from dfdatetime import posix_time as dfdatetime_posix_time
import datetime as dt
import json

class WindowsTimelineActivityEventData(events.EventData):
  """Windows Timeline event data.

  Attributes:
      timeline (str):
  """

  DATA_TYPE = 'windows:timeline:activity'

  def __init__(self):
    """Initializes event data."""
    super(WindowsTimelineActivityEventData, self).__init__(data_type=self.DATA_TYPE)
    self.timeline_data = None

class WindowsTimelineActivityOperationEventData(events.EventData):
  """Windows Timeline event data.

  Attributes:
      timeline (str):
  """

  DATA_TYPE = 'windows:timeline:activityoperation'

  def __init__(self):
    """Initializes event data."""
    super(WindowsTimelineActivityOperationEventData, self).__init__(data_type=self.DATA_TYPE)
    self.timeline_data = None

class WindowsTimelineActivityPackageIdEventData(events.EventData):
  """Windows Timeline event data.

  Attributes:
      timeline (str):
  """

  DATA_TYPE = 'windows:timeline:activitypackageid'

  def __init__(self):
    """Initializes event data."""
    super(WindowsTimelineActivityPackageIdEventData, self).__init__(data_type=self.DATA_TYPE)
    self.timeline_data = None

class WindowsTimelinePluginSqlite(interface.SQLitePlugin):
  """Parse Windows Timeline Files

  Windows Timeline file is stored is a SQLite database file named ActivitiesCache.db
  """

  NAME = 'wintimeline'
  DESCRIPTION = 'Parser for Windows timeline SQLite database files.'

  QUERIES = [
    (('select AppId, ActivityType, ActivityStatus, LastModifiedTime, ExpirationTime, PayLoad, StartTime, EndTime, LastModifiedOnClient, CreatedInCloud from Activity'), 'ParseActivityRow'),
    (('select OperationType, AppId, ActivityType, LastModifiedTime, ExpirationTime, CreatedTime, CreatedInCloud, StartTime, EndTime, LastModifiedOnClient, Payload from ActivityOperation where Id not in (select Id from Activity)'), 'ParseActivityOperationRow'),
    (('select * from Activity_PackageId where Activity_PackageId.ActivityId not in (select Id from Activity) and Activity_PackageId.ActivityId not in (select Id from ActivityOperation)'), 'ParseActivityPackageIdRow')
  ]

  REQUIRED_TABLES = frozenset([
   # 'Activity', 'ActivityOperation',
    'Activity_PackageId'])

  SCHEMAS = [{
    'Activity': (
      'CREATE TABLE [Activity]([Id] GUID PRIMARY KEY NOT NULL, [AppId] '
      'TEXT NOT NULL, [PackageIdHash] TEXT, [AppActivityId] TEXT, '
      '[ActivityType] INT NOT NULL, [ActivityStatus] INT NOT NULL, '
      '[ParentActivityId] GUID, [Tag] TEXT, [Group] TEXT, [MatchId] TEXT, '
      '[LastModifiedTime] DATETIME NOT NULL, [ExpirationTime] DATETIME, '
      '[Payload] BLOB, [Priority] INT, [IsLocalOnly] INT, '
      '[PlatformDeviceId] TEXT, [CreatedInCloud] DATETIME, [StartTime] '
      'DATETIME, [EndTime] DATETIME, [LastModifiedOnClient] DATETIME, '
      '[GroupAppActivityId] TEXT, [ClipboardPayload] BLOB, [EnterpriseId] '
      'TEXT, [OriginalPayload] BLOB, [OriginalLastModifiedOnClient] '
      'DATETIME, [ETag] INT NOT NULL)'),
    'ActivityAssetCache': (
      'CREATE TABLE [ActivityAssetCache]([ResourceId] INTEGER PRIMARY KEY '
      'AUTOINCREMENT NOT NULL, [AppId] TEXT NOT NULL, [AssetHash] TEXT '
      'NOT NULL, [TimeToLive] DATETIME NOT NULL, [AssetUri] TEXT, '
      '[AssetId] TEXT, [AssetKey] TEXT, [Contents] BLOB)'),
    'ActivityOperation': (
      'CREATE TABLE [ActivityOperation]([OperationOrder] INTEGER PRIMARY '
      'KEY ASC NOT NULL, [Id] GUID NOT NULL, [OperationType] INT NOT '
      'NULL, [AppId] TEXT NOT NULL, [PackageIdHash] TEXT, [AppActivityId] '
      'TEXT, [ActivityType] INT NOT NULL, [ParentActivityId] GUID, [Tag] '
      'TEXT, [Group] TEXT, [MatchId] TEXT, [LastModifiedTime] DATETIME '
      'NOT NULL, [ExpirationTime] DATETIME, [Payload] BLOB, [Priority] '
      'INT, [CreatedTime] DATETIME, [Attachments] TEXT, '
      '[PlatformDeviceId] TEXT, [CreatedInCloud] DATETIME, [StartTime] '
      'DATETIME NOT NULL, [EndTime] DATETIME, [LastModifiedOnClient] '
      'DATETIME NOT NULL, [CorrelationVector] TEXT, [GroupAppActivityId] '
      'TEXT, [ClipboardPayload] BLOB, [EnterpriseId] TEXT, '
      '[OriginalPayload] BLOB, [OriginalLastModifiedOnClient] DATETIME, '
      '[ETag] INT NOT NULL)'),
    'Activity_PackageId': (
      'CREATE TABLE [Activity_PackageId]([ActivityId] GUID NOT NULL, '
      '[Platform] TEXT NOT NULL, [PackageName] TEXT NOT NULL, '
      '[ExpirationTime] DATETIME NOT NULL)'),
    'AppSettings': (
      'CREATE TABLE [AppSettings]([AppId] TEXT PRIMARY KEY NOT NULL, '
      '[SettingsPropertyBag] BLOB, [AppTitle] TEXT, [Logo4141] TEXT)'),
    'ManualSequence': (
      'CREATE TABLE [ManualSequence]([Key] TEXT PRIMARY KEY NOT NULL, '
      '[Value] INT NOT NULL)'),
    'Metadata': (
      'CREATE TABLE [Metadata]([Key] TEXT PRIMARY KEY NOT NULL, [Value] '
      'TEXT)')}]

  def ParseActivityRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a activity row from database

    :param parser_mediator:
    :param query:
    :param row:
    :param unused_kwargs:
    :return:
    """
    query_hash = hash(query)
    event_data = WindowsTimelineActivityEventData()

    appId = self._GetRowValue(query_hash, row, "AppId").split(",")
    actType = self._GetRowValue(query_hash, row, "ActivityType")
    actStatus = self._GetRowValue(query_hash, row, "ActivityStatus")

    lmTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "LastModifiedTime"))
    expTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "ExpirationTime"))
    lmcliTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "LastModifiedOnClient"))
    if self._GetRowValue(query_hash, row, "CreatedInCloud") == 0:
      creTime = "No Create In Cloud"
    else:
      creTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "CreatedInCloud"))
    if self._GetRowValue(query_hash, row, "EndTime") == 0:
      endTime = "None"
    else:
      endTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "EndTime"))
    staTime = str(self._GetRowValue(query_hash, row, "StartTime"))

    if actType == 5: actType = "Open App/File/Url"
    elif actType == 6: actType = "App In Focus"
    else: actType = "Unknown"

    if actStatus == 1: actStatus = "Active"
    elif actStatus == 2: actStatus = "Update"
    elif actStatus == 3: actStatus = "Deleted"
    elif actStatus == 4: actStatus = "Ignore"
    else: actStatus = "Unknown"

    payload_bytes = bytes(self._GetRowValue(query_hash, row, "Payload"))
    payload_string = payload_bytes.decode('utf-8')
    payload = json.loads(payload_string)

    data = "[Program]: " + appId[0].split('":"')[1][:-1]
#    data += " [Platform]: " + appId[1].split('":"')[1][:-1]
    data += " [Active Type]: " + actType
    data += " [Active Status]: " + actStatus
    data += " [LastModifiedTime]: " + str(lmTime)
    data += " [EndTime]: " + str(endTime)
    data += " [ExpirationTime]: " + str(expTime)
    data += " [CreateInCloud]: " + str(creTime)
    data += " [LastModifiedOnClientTime]: " + str(lmcliTime)

    if 'description' in payload:
      data += " [appDisplayName]: " + payload['appDisplayName']
      data += " [content]: " + payload['contentUri']
      data += " [displayText]: " + payload['displayText']
      data += " [description]: " + payload['description']

    event_data.timeline_data = data
    event_data.query = query

    date_time = dfdatetime_posix_time.PosixTime(timestamp=staTime)
    event = time_events.DateTimeValuesEvent(date_time, definitions.TIME_DESCRIPTION_START)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseActivityOperationRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a activity operation row from database

    :param parser_mediator:
    :param query:
    :param row:
    :param unused_kwargs:
    :return:
    """
    query_hash = hash(query)
    event_data = WindowsTimelineActivityOperationEventData()

    appId = self._GetRowValue(query_hash, row, "AppId").split(",")
    operType = self._GetRowValue(query_hash, row, "OperationType")
    if operType == 1: operType = "Active"
    elif operType == 2: operType = "Updated"
    elif operType == 3: operType = "Deleted"
    elif operType == 4: operType = "Ignore"
    else: operType = "Unknown"

    actType = self._GetRowValue(query_hash, row, "ActivityType")
    if actType == 5: actType = "Open App/File/Url"
    elif actType == 6: actType = "App In Focus"
    else: actType = "Unknown"

    lmTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "LastModifiedTime"))
    expTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "ExpirationTime"))
    lmcliTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "LastModifiedOnClient"))
    creaTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "CreatedTime"))
    if self._GetRowValue(query_hash, row, "CreatedInCloud") == 0:
      creTime = "No Create In Cloud"
    else:
      creTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "CreatedInCloud"))
    if self._GetRowValue(query_hash, row, "EndTime") == 0:
      endTime = "None"
    else:
      endTime = dt.datetime.fromtimestamp(self._GetRowValue(query_hash, row, "EndTime"))
    staTime = str(self._GetRowValue(query_hash, row, "StartTime"))

    payload_bytes = bytes(self._GetRowValue(query_hash, row, "Payload"))
    payload_string = payload_bytes.decode('utf-8')
    payload = json.loads(payload_string)

    data = "[Program]: " + appId[0].split('":"')[1][:-1]
#    data += " [Platform]: " + appId[1].split('":"')[1][:-1]
    data += " [Active Type]: " + operType
    data += " [Active Status]: " + actType
    data += " [LastModifiedTime]: " + str(lmTime)
    data += " [CreateTime]: " + str(creaTime)
    data += " [EndTime]: " + str(endTime)
    data += " [ExpirationTime]: " + str(expTime)
    data += " [CreateInCloud]: " + str(creTime)
    data += " [LastModifiedOnClientTime]: " + str(lmcliTime)

    if 'description' in payload:
      data += " [appDisplayName]: " + payload['appDisplayName']
      data += " [content]: " + payload['contentUri']
      data += " [displayText]: " + payload['displayText']
      data += " [description]: " + payload['description']

    event_data.timeline_data = data
    event_data.query = query

    date_time = dfdatetime_posix_time.PosixTime(timestamp=staTime)
    event = time_events.DateTimeValuesEvent(date_time, definitions.TIME_DESCRIPTION_START)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseActivityPackageIdRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a activity packageid row from database

    :param parser_mediator:
    :param query:
    :param row:
    :param unused_kwargs:
    :return:
    """
    query_hash = hash(query)
    event_data = WindowsTimelineActivityPackageIdEventData()

    data = "FileName: " + self._GetRowValue(query_hash, row, 'PackageName')
    data += " Platform: " + self._GetRowValue(query_hash, row, 'Platform')
    data += " ExpirationTime: " + str(self._GetRowValue(query_hash, row, 'ExpirationTime'))
    event_data.timeline_data = data

    date_time = dfdatetime_semantic.SemanticTime('Not set')
    event = time_events.DateTimeValuesEvent(date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
    parser_mediator.ProduceEventWithEventData(event, event_data)

sqlite.SQLiteParser.RegisterPlugin(WindowsTimelinePluginSqlite)
