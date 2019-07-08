# -*- coding: utf-8 -*-
"""The database configuration CLI arguments helper."""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.cli.helpers import interface
from plaso.cli.helpers import server_config
from plaso.cli.helpers import manager


class DatabaseArgumentsHelper(interface.ArgumentsHelper):
  """Database configuration CLI arguments helper."""

  NAME = 'database_config'
  DESCRIPTION = 'Argument helper for a database configuration.'

  _DEFAULT_NAME = 'data'
  _DEFAULT_PASSWORD = 'toor'
  _DEFAULT_USERNAME = 'root'

  @classmethod
  def AddArguments(cls, argument_group):
    """Adds command line arguments the helper supports to an argument group.

    This function takes an argument parser or an argument group object and adds
    to it all the command line arguments this helper supports.

    Args:
      argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
          argparse group.
    """
    argument_group.add_argument(
        '--user', dest='username', type=str, action='store',
        default=cls._DEFAULT_USERNAME, metavar='USERNAME', required=False,
        help='The username used to connect to the database.')
    argument_group.add_argument(
        '--password', dest='password', type=str, action='store',
        default=cls._DEFAULT_PASSWORD, metavar='PASSWORD', help=(
            'The password for the database user.'))
    argument_group.add_argument(
        '--db_name', '--db-name', dest='db_name', action='store',
        type=str, default=cls._DEFAULT_NAME, required=False, help=(
            'The name of the database to connect to.'))
    argument_group.add_argument(
        '--case_id', '--case-number', dest='case_id', action='store',
        type=str, default='', required=False, help=(
            'The number of the case.'))
    argument_group.add_argument(
        '--evd_id', '--evidence-number', dest='evd_id', action='store',
        type=str, default='', required=False, help=(
            'The number of the evidence.'))
    argument_group.add_argument(
        '--par_id', '--partition-number', dest='par_id', action='store',
        type=str, default='', required=False, help=(
            'The number of the partition of the evidence.'))

    server_config.ServerArgumentsHelper.AddArguments(argument_group)

  # pylint: disable=arguments-differ
  @classmethod
  def ParseOptions(cls, options, output_module):
    """Parses and validates options.

    Args:
      options (argparse.Namespace): parser options.
      output_module (OutputModule): output module to configure.

    Raises:
      BadConfigObject: when the output module object does not have the
          SetCredentials or SetDatabaseName methods.
    """
    if not hasattr(output_module, 'SetCredentials'):
      raise errors.BadConfigObject('Unable to set username information.')

    if not hasattr(output_module, 'SetDatabaseName'):
      raise errors.BadConfigObject('Unable to set database information.')

    if not hasattr(output_module, 'SetCaseInformation'):
      raise errors.BadConfigObject('Unable to set case information.')

    username = cls._ParseStringOption(
        options, 'username', default_value=cls._DEFAULT_USERNAME)
    password = cls._ParseStringOption(
        options, 'password', default_value=cls._DEFAULT_PASSWORD)
    name = cls._ParseStringOption(
        options, 'db_name', default_value=cls._DEFAULT_NAME)
    case_id = cls._ParseStringOption(
        options, 'case_id', default_value='')
    evd_id = cls._ParseStringOption(
        options, 'evd_id', default_value='')
    par_id = cls._ParseStringOption(
        options, 'par_id', default_value='')
    output_module.SetCredentials(username=username, password=password)
    output_module.SetDatabaseName(name)
    output_module.SetCaseInformation(case_id, evd_id, par_id)
    server_config.ServerArgumentsHelper.ParseOptions(options, output_module)