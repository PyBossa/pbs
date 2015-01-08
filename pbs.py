#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.
"""
A very simple PyBossa command line client.

This module is a pybossa-client that runs the following commands:

    * create_project: to create a PyBossa project
    * add_tasks: to add tasks to an existing project
    * delete_tasks: to delete all tasks and task_runs from an existing project

"""

import click
import pbclient
import simplejson as json
from simplejson import JSONDecodeError
import jsonschema
import ConfigParser
import os.path
from os.path import expanduser
from helpers import *


class Config(object):

    """Config class for the command line."""

    def __init__(self):
        """Init the configuration default values."""
        self.verbose = False
        self.server = None
        self.api_key = None
        self.project = None
        self.pbclient = pbclient
        self.parser = ConfigParser.ConfigParser()

pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--server',  help='The PyBossa server')
@click.option('--api-key', help='Your PyBossa API-KEY')
@click.option('--credentials', help='Use your PyBossa credentials in .pybossa.cfg file',
              default="default")
@click.option('--project', type=click.File('r'), default='project.json')
@pass_config
def cli(config, server, api_key, credentials, project):
    """Create the cli command line."""
    # Check first for the pybossa.rc file to configure server and api-key
    home = expanduser("~")
    if os.path.isfile(os.path.join(home, '.pybossa.cfg')):
        config.parser.read(os.path.join(home, '.pybossa.cfg'))
        config.server = config.parser.get(credentials,'server')
        config.api_key = config.parser.get(credentials, 'apikey')
    if server:
        config.server = server
    if api_key:
        config.api_key = api_key
    try:
        config.project = json.loads(project.read())
    except JSONDecodeError as e:
        click.secho("Error: invalid JSON format in project.json:", fg='red')
        if e.msg == 'Expecting value':
            e.msg += " (if string enclose it with double quotes)"
        click.echo("%s\n%s: line %s column %s" % (e.doc, e.msg, e.lineno, e.colno))
        raise click.Abort()
    try:
        project_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "short_name": {"type": "string"},
                "description": {"type": "string"}
            }
        }
        jsonschema.validate(config.project, project_schema)
    except jsonschema.exceptions.ValidationError as e:
        click.secho("Error: invalid type in project.json", fg='red')
        click.secho("'%s': %s" % (e.path[0], e.message), fg='yellow')
        click.echo("'%s' must be a %s" % (e.path[0], e.validator_value))
        raise click.Abort()

    config.pbclient = pbclient
    config.pbclient.set('endpoint', config.server)
    config.pbclient.set('api_key', config.api_key)


@cli.command()
@pass_config
def version(config):
    """Show pbs version."""
    try:
        import pkg_resources
        click.echo(pkg_resources.get_distribution('pybossa-pbs').version)
    except:
        click.echo("pybossa-pbs package not found!")


@cli.command()
@pass_config
def create_project(config): # pragma: no cover
    """Create the PyBossa project."""
    res = _create_project(config)
    click.echo(res)


@cli.command()
@click.option('--task-presenter', help='The project task presenter file',
              type=click.File('r'), default='template.html')
@click.option('--long-description', help='The project long description file (Markdown)',
              type=click.File('r'), default='long_description.md')
@click.option('--tutorial', help='The project tutorial file',
              type=click.File('r'), default='tutorial.html')
@pass_config
def update_project(config, task_presenter, long_description, tutorial): # pragma: no cover
    """Update project templates and information."""
    res = _update_project(config, task_presenter, long_description, tutorial)
    click.echo(res)


@cli.command()
@click.option('--tasks-file', help='File with tasks',
              default='project.tasks', type=click.File('r'))
@click.option('--tasks-type', help='Tasks type: JSON|CSV|PO|PROPERTIES',
              default='json', type=click.Choice(['json', 'csv', 'po',
                                                 'properties']))
@click.option('--priority', help="Priority for the tasks.", default=0)
@click.option('--redundancy', help="Redundancy for tasks.", default=30)
@pass_config
def add_tasks(config, tasks_file, tasks_type, priority, redundancy):
    """Add tasks to a project."""
    res = _add_tasks(config, tasks_file, tasks_type, priority, redundancy)
    click.echo(res)

@cli.command()
@click.option('--task-id', help='Task ID to delete from project', default=None)
@pass_config
def delete_tasks(config, task_id):
    """Delete tasks from a project."""
    if task_id is None:
        msg = ("Are you sure you want to delete all the tasks and associated task runs?")
        if click.confirm(msg):
            res = _delete_tasks(config, task_id)
            click.echo(res)

        else:
            click.echo("Aborting.")
    else:
        res = _delete_tasks(config, task_id)
        click.echo(res)

@cli.command(name='update-task-redundancy')
@click.option('--task-id', help='Task ID to update from project', default=None)
@click.option('--redundancy', help='New redundancy for task', default=None)
@pass_config
def update_task_redundancy(config, task_id, redundancy):
    """Update task redudancy for a project."""
    if task_id is None:
        msg = ("Are you sure you want to update all the tasks redundancy?")
        if click.confirm(msg):
            res = _update_tasks_redundancy(config, task_id, redundancy)
            click.echo(res)

        else:
            click.echo("Aborting.")
    else:
        res = _update_tasks_redundancy(config, task_id, redundancy)
        click.echo(res)
