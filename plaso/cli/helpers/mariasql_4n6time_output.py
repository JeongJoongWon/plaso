# -*- coding: utf-8 -*-
"""The 4n6time SQLite database output module CLI arguments helper."""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import database_config
from plaso.cli.helpers import shared_4n6time_output
from plaso.cli.helpers import manager
from plaso.output import mariasql_4n6time

class Maria4n6TimeDatabaseArgumentsHelper(
    database_config.DatabaseArgumentsHelper):

    _DEFAULT_USERNAME = 'root'
    _DEFAULT_PASSWORD = 'forensic'

class MariaSQL4n6TimeOutputArgumentsHelper(interface.ArgumentsHelper):
    """MariaSQL4n6TimeOutputArgumentsHelper output module argument helper
    """
    NAME = '4n6time_maria'
    CATEGORY = 'output'
    DESCRIPTION = 'Argument helper for the 4n6Time Maria database output module.'

    @classmethod
    def AddArguments(cls, argument_group):
        """
        AddArguments add to argument group
        :param argument_group:
        """
        shared_4n6time_output.Shared4n6TimeOutputArgumentsHelper.AddArguments(argument_group)
        Maria4n6TimeDatabaseArgumentsHelper.AddArguments(argument_group)

    @classmethod
    def ParseOptions(cls, options, output_module):
        """
        ParseOptions instance mariasql_4n6time
        :param options:
        :param output_module:
        :return:
        """
        if not isinstance(output_module, mariasql_4n6time.MariaSQL4n6TimeOutputMoudle):
            raise errors.BadConfigObject(
                "Output module is not an instance of MariaSQL4n6TimeOutputModule")

        Maria4n6TimeDatabaseArgumentsHelper.ParseOptions(options, output_module)
        shared_4n6time_output.Shared4n6TimeOutputArgumentsHelper.ParseOptions(options, output_module)

manager.ArgumentHelperManager.RegisterHelper(MariaSQL4n6TimeOutputArgumentsHelper)