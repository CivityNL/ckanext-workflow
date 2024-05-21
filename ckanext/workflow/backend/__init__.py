from ckan.plugins import toolkit
from typing import Callable, Dict, List
from ckanext.workflow.backend.validators import is_function_with_parameters as _is_function_with_parameters_validator
import ckanext.workflow.constants as workflow_constants
from ckan.authz import users_role_for_group_or_org, has_user_permission_for_group_or_org, user_is_collaborator_on_dataset, is_sysadmin

from ckanext.workflow.backend.workflow import WorkflowBackend

# logging
import logging
log = logging.getLogger(__name__)


_Invalid = toolkit.Invalid
_check_access = toolkit.check_access


def scheming_language_text(text, prefer_lang=None):
    """
    :param text: {lang: text} dict or text string
    :param prefer_lang: choose this language version if available

    Convert "language-text" to users' language by looking up
    languag in dict or using gettext if not a dict
    """
    if not text:
        return u''

    assert text != {}
    if hasattr(text, 'get'):
        try:
            if prefer_lang is None:
                prefer_lang = lang()
        except TypeError:
            pass  # lang() call will fail when no user language available
        else:
            try:
                return text[prefer_lang]
            except KeyError:
                pass

        default_locale = config.get('ckan.locale_default', 'en')
        try:
            return text[default_locale]
        except KeyError:
            pass

        l, v = sorted(text.items())[0]
        return v

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')
    t = _(text)
    return t


def is_function(value):
    result = True
    try:
        _is_function_with_parameters_validator(["context", "pkg_dict"])(value)
    except _Invalid:
        result = False
    return result
