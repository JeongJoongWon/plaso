# -*- coding: utf-8 -*-
"""Defines the output module for the SQLite database used by 4n6time."""

from __future__ import unicode_literals

import os

try:
    import pymysql
except ImportError:
    pymysql = None

from plaso.output import logger
from plaso.output import manager
from plaso.output import shared_4n6time

import pdb

class MariaSQL4n6TimeOutputMoudle(shared_4n6time.Shared4n6TimeOutputModule):
    """Output module class to save the data in a Maria database
    """
    NAME = "4n6time_maria"
    DESCRIPTION = (
        "Saves the data in a Maria database, used by the tool 4n6time.")

    _META_FIELDS = frozenset([
        'sourcetype', 'source', 'user', 'host', 'MACB', 'type',
        'record_number'])

    _CREATE_TABLE_QUERY = (
        'CREATE TABLE IF NOT EXISTS log2timeline ('
        'rowid INT NOT NULL AUTO_INCREMENT, timezone VARCHAR(256), '
        'MACB VARCHAR(256), source VARCHAR(256), sourcetype VARCHAR(256), '
        'type VARCHAR(256), user VARCHAR(256), host VARCHAR(256), '
        'description LONGBLOB, filename VARCHAR(256), inode VARCHAR(256), '
        'notes VARCHAR(256), format VARCHAR(256), '
        'extra TEXT, datetime datetime, reportnotes VARCHAR(256), '
        'inreport VARCHAR(256), tag VARCHAR(256), offset INT, '
        'vss_store_number INT, URL TEXT, record_number VARCHAR(256), '
        'event_identifier VARCHAR(256), event_type VARCHAR(256), '
        'source_name VARCHAR(256), user_sid VARCHAR(256), '
        'computer_name VARCHAR(256), evidence VARCHAR(256), '
        'case_id VARCHAR(256), evd_id VARCHAR(256), par_id VARCHAR(256), '
        'PRIMARY KEY (rowid))')

    def __init__(self, output_meidator):
        """MariaSQL4n6TimeOutputModule class constructor
        Constructor
        :param output_meidator: output meidator
        """
        super(MariaSQL4n6TimeOutputMoudle, self).__init__(output_meidator)
        self._connection = None
        self._count = None
        self._cursor = None
        self._dbname = None
        self._host = None
        self._user = None
        self._password = None
        self._port = None
        self._case_id = None
        self._evd_id = None
        self._par_id = None

    def _GetTags(self):
        """
        _GetTags Retrieves tags from the database.
        :return: list of tags
        """
        all_tags = []
        self._cursor.execute('SELECT DISTINCT tag FROM log2timeline')

        # This cleans up the messy SQL return.
        tag_row = self._cursor.fetchone()
        while tag_row:
            tag_string = tag_row[0]
            if tag_string:
                tags = tag_string.split(',')
                for tag in tags:
                    if tag not in all_tags:
                        all_tags.append(tag)
            tag_row = self._cursor.fetchone()

        # TODO: make this method an iterator.
        return all_tags

    def _GetUniqueValues(self, field_name):
        """
        _GetUniqueValues Retrieves the unique values of a specific field from the database.
        :param field_name: name of the field.
        :return: dict[str, int]: number of instances of the field value per field name.
        """
        self._cursor.execute(
            'SELECT {0:s}, COUNT({0:s}) FROM log2timeline GROUP BY {0:s}'.format(
                field_name))

        result = {}
        row = self._cursor.fetchone()
        while row:
            if row[0]:
                result[row[0]] = row[1]

            row = self._cursor.fetchone()

        return result

    def Close(self):
        """
        Close database connection close
        """
        """
        if not self._append:
            for field_name in self._fields:
                query = 'CREATE INDEX {0:s}_idx ON log2timeline ({0:s})'.format(
                    field_name)
                self._cursor.execute(query)
                if self._set_status:
                    self._set_status('Created index: {0:s}'.format(field_name))

        # Get meta info and save into their tables.
        if self._set_status:
            self._set_status('Creating metadata...')

        for field in self._META_FIELDS:
            values = self._GetUniqueValues(field)
            self._cursor.execute('DELETE FROM l2t_{0:s}s'.format(field))
            for name, frequency in iter(values.items()):
                self._cursor.execute((
                                         'INSERT INTO l2t_{0:s}s ({1:s}s, frequency) '
                                         'VALUES("{2:s}", {3:d}) ').format(field, field, name, frequency))

        self._cursor.execute('DELETE FROM l2t_tags')
        for tag in self._GetTags():
            self._cursor.execute(
                'INSERT INTO l2t_tags (tag) VALUES ("{0:s}")'.format(tag))

        if self._set_status:
            self._set_status('Database created.')

        self._connection.commit()
        """
        self._cursor.close()
        self._connection.close()

        self._cursor = None
        self._connection = None

    def Open(self):
        """
        Open database connection open and initialize
        :raises ValueError: missing database name
        :raises pymysql.Error: Unable action
        """
        if not self._dbname:
            raise ValueError('Missing database name.')

        try:
            self._connection = pymysql.connect(
                host=self._host, port=self._port, user=self._user, password=self._password)
            self._connection.set_charset('utf8mb4')
            self._cursor = self._connection.cursor()
            
            self._cursor.execute(
                'CREATE DATABASE IF NOT EXISTS {0:s}'.format(self._dbname))
            self._cursor.execute('USE {0:s}'.format(self._dbname))
            self._cursor.close()
            self._connection.close()

            self._connection = pymysql.connect(
                host = self._host, port = self._port,
                user = self._user, password = self._password, database = self._dbname)
            self._connection.set_charset('utf8mb4')
            self._cursor = self._connection.cursor()

            self._cursor.execute('SET NAMES utf8mb4')
            self._cursor.execute('SET CHARACTER SET utf8mb4')
            self._cursor.execute('SET character_set_connection=utf8mb4')

            # Create tables.
            self._cursor.execute(self._CREATE_TABLE_QUERY)
            if self._set_status:
                self._set_status('Created table: log2timeline')
            """
            for field in self._META_FIELDS:
                self._cursor.execute(
                    'CREATE TABLE IF NOT EXISTS l2t_{0}s ({0}s TEXT, frequency INT)'
                    .format(field))
                if self._set_status:
                    self._set_status('Created table: l2t_{0:s}'.format(field))
            
            self._cursor.execute(
                'CREATE TABLE IF NOT EXISTS l2t_tags (tag TEXT)')
            if self._set_status:
                self._set_status('Created table: l2t_tags')

            self._cursor.execute(
                'CREATE TABLE IF NOT EXISTS l2t_saved_query ('
                'name TEXT, query TEXT)')
            if self._set_status:
                self._set_status('Created table: l2t_saved_query')

            self._cursor.execute(
                'CREATE TABLE IF NOT EXISTS l2t_disk ('
                'disk_type INT, mount_path TEXT, '
                'dd_path TEXT, dd_offset TEXT, '
                'storage_file TEXT, export_path TEXT)')

            self._cursor.execute(
                'INSERT INTO l2t_disk ('
                'disk_type, mount_path, dd_path, '
                'dd_offset, storage_file, '
                'export_path) VALUES '
                '(0, "", "", "", "", "")')
            
            if self._set_status:
                self._set_status('Created table: l2t_disk')
            """
        except pymysql.Error as exception:
            raise IOError('Unable to insert into database with error: {0!s}'.format(
                exception))

        self._count = 0
    
    def WriteEventBody(self, event, event_data, event_tag):
        """
        WriteEventBody write event data at database
        :param event:
        :return:
        :raises pymysql.Error: Unable action
        """

        if not hasattr(event, 'timestamp'):
            return

        row = self._GetSanitizedEventValues(event, event_data, event_tag)
        if row['datetime'] == 'N/A':
            row['datetime'] = '1900-01-01 00:00:00.000'

        row['case_id'] = self._case_id
        row['evd_id'] = self._evd_id
        row['par_id'] = self._par_id

        _INSERT_QUERY = (
            'INSERT INTO log2timeline(timezone, MACB, source, '
            'sourcetype, type, user, host, description, filename, '
            'inode, notes, format, extra, datetime, reportnotes, inreport, '
            'tag, offset, vss_store_number, URL, record_number, '
            'event_identifier, event_type, source_name, user_sid, computer_name, '
            'evidence, case_id, evd_id, par_id) '
            'VALUES (%(timezone)s, %(MACB)s, %(source)s, %(sourcetype)s, %(type)s, %(user)s, %(host)s, '
            '%(description)s, %(filename)s, %(inode)s, %(notes)s, %(format)s, %(extra)s, %(datetime)s, '
            '%(reportnotes)s, %(inreport)s, %(tag)s, %(offset)s, %(vss_store_number)s, %(URL)s, '
            '%(record_number)s, %(event_identifier)s, %(event_type)s, %(source_name)s, '
            '%(user_sid)s, %(computer_name)s, %(evidence)s, %(case_id)s, '
            '%(evd_id)s, %(par_id)s)')

        try:
            self._cursor.execute(_INSERT_QUERY, row)
        except pymysql.Error as exception:
            logger.warning(
                'Unable to insert into database with error: {0!s}.'.format(
                    exception))
            print(row['description'])

        self._count += 1

        # TODO: Experiment if committing the current transaction
        # every 10000 inserts is the optimal approach.
        if self._count % 10000 == 0:
            self._connection.commit()
            if self._set_status:
                self._set_status('Inserting event: {0:d}'.format(self._count))


    def WriteEventBody_old(self, event):
        """
        WriteEventBody write event data at database
        :param event:
        :return:
        :raises pymysql.Error: Unable action
        """

        if not hasattr(event, 'timestamp'):
            return

        row = self._GetSanitizedEventValues(event)
        if row['datetime'] == 'N/A':
            row['datetime'] = '1900-01-01 00:00:00.000'

        row['case_id'] = self._case_id
        row['evd_id'] = self._evd_id
        row['par_id'] = self._par_id

        _INSERT_QUERY = (
            'INSERT INTO log2timeline(timezone, MACB, source, '
            'sourcetype, type, user, host, description, filename, '
            'inode, notes, format, extra, datetime, reportnotes, inreport, '
            'tag, offset, vss_store_number, URL, record_number, '
            'event_identifier, event_type, source_name, user_sid, computer_name, '
            'evidence, case_id, evd_id, par_id) '
            'VALUES (%(timezone)s, %(MACB)s, %(source)s, %(sourcetype)s, %(type)s, %(user)s, %(host)s, '
            '%(description)s, %(filename)s, %(inode)s, %(notes)s, %(format)s, %(extra)s, %(datetime)s, '
            '%(reportnotes)s, %(inreport)s, %(tag)s, %(offset)s, %(vss_store_number)s, %(URL)s, '
            '%(record_number)s, %(event_identifier)s, %(event_type)s, %(source_name)s, '
            '%(user_sid)s, %(computer_name)s, %(evidence)s, %(case_id)s, '
            '%(evd_id)s, %(par_id)s)')

        try:
            pdb.set_trace()
            self._cursor.execute(_INSERT_QUERY, row)
        except pymysql.Error as exception:
            logger.warning(
                'Unable to insert into database with error: {0!s}.'.format(
                    exception))
            print(row['description'])

        self._count += 1

        # TODO: Experiment if committing the current transaction
        # every 10000 inserts is the optimal approach.
        if self._count % 10000 == 0:
            self._connection.commit()
            if self._set_status:
                self._set_status('Inserting event: {0:d}'.format(self._count))

    def SetCredentials(self, password=None, username=None):
        """Sets the database credentials.

        Args:
          password (Optional[str]): password to access the database.
          username (Optional[str]): username to access the database.
        """
        if password:
            self._password = password
        if username:
            self._user = username

    def SetDatabaseName(self, name):
        """Sets the database name.

        Args:
          name (str): name of the database.
        """
        self._dbname = name

    def SetServerInformation(self, server, port):
        """Sets the server information.

        Args:
          server (str): hostname or IP address of the database server.
          port (int): port number of the database server.
        """
        self._host = server
        self._port = port

    def SetCaseInformation(self, case_id, evd_id, par_id):
        self._case_id = case_id
        self._evd_id = evd_id
        self._par_id = par_id

manager.OutputManager.RegisterOutput(MariaSQL4n6TimeOutputMoudle)