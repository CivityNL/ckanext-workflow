from ckanext.workflow.backend.validators import is_function_with_parameters as _is_function_with_parameters_validator
from ckanext.workflow.backend.workflow import WorkflowBackend
from ckanext.workflow.common import Invalid, getLogger

log = getLogger(__name__)


def is_function(value):
    result = True
    try:
        _is_function_with_parameters_validator(["context", "pkg_dict"])(value)
    except Invalid:
        result = False
    return result
