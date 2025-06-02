import inspect
import json
import os
from json import JSONDecodeError

import requests
import yaml
from requests import RequestException
from yaml import YAMLError

import ckanext.workflow.common as common
import logging

log = logging.getLogger(__name__)


def get_context(for_view=None):
    _context = {
        'model': common.model,
        'session': common.model.Session,
        'user': common.g.user,
        'for_view': True,
        'auth_user_obj': common.g.userobj
    }
    if for_view is not None:
        _context['for_view'] = for_view
    return _context


def sphinx_decorator(decorator, wrapper, method, extra_message=None):
    # making sure decorated methods are handled correctly by Sphinx and prepend the docstring with a mention
    wrapper.__name__ = method.__name__
    wrapper.__module__ = method.__module__

    doc_string = "@decorated with :py:func:`~{}.{}`.".format(decorator.__module__, decorator.__name__)
    if extra_message is not None:
        doc_string += extra_message

    wrapper.__doc__ = "{}\n{}".format(doc_string, method.__doc__)


def load_workflow_specification_file(path):
    result = None
    if os.path.exists(path):
        with open(path) as file:
            result = file.read()
    return result


def load_workflow_specification(config_option):
    specification_url = common.config.get(config_option, None)

    specification = None
    exception = None

    if not specification_url:
        msg = "Empty or missing value for the workflow specification at '{}'".format(config_option)
        raise Exception(msg)

    if specification_url.startswith(('http://', 'https://')):
        # dealing with an URL
        try:
            response = requests.get(specification_url)
            specification = response.content.decode()
        except RequestException as request_exception:
            exception = request_exception
    elif specification_url.startswith('file://'):
        # dealing with a local file
        specification_path = specification_url.replace('file://', '')
        specification = load_workflow_specification_file(specification_path)
    elif ':' in specification_url:
        # (possibly) dealing with module path
        specification_module_name, specification_path = specification_url.split(':', 1)
        try:
            specification_module = __import__(specification_module_name, fromlist=[''])
            specification_path = os.path.join(os.path.dirname(inspect.getfile(specification_module)),
                                              specification_path)
            specification = load_workflow_specification_file(specification_path)
        except ImportError as import_error:
            exception = import_error

    if specification is None:
        msg = "Couldn't get the workflow specification file from {}: {}".format(specification_url, exception)
        raise Exception(msg)

    if specification_url.lower().endswith(('.yaml', '.yml')):
        try:
            return yaml.safe_load(specification)
        except YAMLError as yaml_error:
            msg = "Couldn't parse the workflow specification file using YAML from {}".format(specification_url,
                                                                                             yaml_error)
            raise Exception(msg)
    else:
        try:
            return json.loads(specification)
        except JSONDecodeError as json_error:
            msg = "Couldn't parse the workflow specification file using JSON from {}".format(specification_url,
                                                                                             json_error)
            raise Exception(msg)
