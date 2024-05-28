from ckanext.authorization.monkey_patch.authz import has_user_permission_for_dataset
from ckanext.workflow.backend.validators import is_function_with_parameters
from ckanext.workflow.common import Invalid, is_sysadmin

def is_function(value):
    result = True
    try:
        is_function_with_parameters(["context", "pkg_dict"])(value)
    except Invalid:
        result = False
    return result


class _WorkflowObject(object):

    def __repr__(self):
        attribute_repr = []
        for k in self.__dict__:
            v = self.__dict__.get(k)
            if isinstance(v, list):
                attribute_repr.append("{}[{}]:{}".format(k, len(v), v))
            else:
                attribute_repr.append("{}:{}".format(k, v))
        return f"<{self.__class__.__name__} {' '.join(attribute_repr)}>"


class WorkflowState(_WorkflowObject):
    id = None
    _label = None
    dataset_fields = None
    update_actions = None

    @property
    def label(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self._label()

    def __init__(self, **kwargs):
        kwargs["_label"] = kwargs.pop("label", None)
        self.__dict__.update(kwargs)


    def update_action_allowed(self, update_action, user_id, pkg_id):
        update_actions = {ua.get('permission'): ua.get('to_state', None) for ua in self.update_actions if ua.get('action') == update_action}
        result = False
        for permission in update_actions:
            if has_user_permission_for_dataset(user_id, permission, pkg_id):
                result = True
                break
        return result

    def state_after_update_action(self, update_action, user_id, pkg_id):

        print(f"state_after_update_action(update_action={update_action}, user_id={user_id}, pkg_id={pkg_id})")

        update_actions = {ua.get('permission'): ua.get('to_state', None) for ua in self.update_actions if ua.get('action') == update_action}

        result = None
        for permission in update_actions:
            if has_user_permission_for_dataset(user_id, permission, pkg_id):
                result = update_actions[permission]
                break
        if result is None:
            result = self.id
        print(f"state_after_update_action -> {result}")
        return result

    def update_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_update, user_id, pkg_id, org_id)

    def validate(self, pkg_dict):
        pkg_fields = {f: pkg_dict.get(f) for f in pkg_dict if f != 'extras'}
        pkg_extra_fields = {extra.get('key'): extra.get('value') for extra in pkg_dict.get('extras', [])}
        errors = {}
        if self.dataset_fields:
            for field in self.dataset_fields:
                field_value = self.dataset_fields[field]
                if field in pkg_fields:
                    value = pkg_fields.get(field)
                elif field in pkg_extra_fields:
                    value = pkg_extra_fields.get(field)
                else:
                    errors[field] = ['Missing']
                    continue
                if field_value != value:
                    errors[field] = ['Expected {field_value} but got {value}'.format(
                        field_value=field_value, value=value
                    )]
        return errors

    def _check_allowed(self, context, checks, user_id, pkg_id, org_id):
        # print(f"WorkflowState._check_allowed for checks={checks}, user_id={user_id}, pkg_id={pkg_id}, org_id={org_id}")
        result = is_sysadmin(user_id)
        for check in checks:
            if result:
                break
            if is_function(check):
                result = check(context=context, pkg_dict=None)
            elif check in workflow_constants.CAPACITIES:
                result = users_role_for_group_or_org(org_id, user_id) == check
                if not result:
                    result = user_is_collaborator_on_dataset(user_id, pkg_id, check)
            elif check in workflow_constants.PERMISSIONS:
                result = has_user_permission_for_group_or_org(org_id, user_id,
                                                              check.split(workflow_constants.PERMISSION_PREFIX, 1)[1])
        return result


class WorkflowTransition(_WorkflowObject):
    from_state = None
    to_state = None
    can_request = []
    can_approve = []
    can_assign = []
    request_message_required = None
    approve_message_required = None
    reject_message_required = None
    _label = None

    @property
    def label(self):
        return self._label()


    def __init__(self, **kwargs):
        kwargs["_label"] = kwargs.pop("label", None)
        self.__dict__.update(kwargs)

    def _check_allowed(self, context, checks, user_id, pkg_id, org_id):
        # print(f"WorkflowTransition._check_allowed for checks={checks}, user_id={user_id}, pkg_id={pkg_id}, org_id={org_id}")
        result = is_sysadmin(user_id)
        for check in checks:
            if result:
                break
            if is_function(check):
                result = check(context=context, pkg_dict=None)
            else:
                result = has_user_permission_for_dataset(user_id, check, pkg_id)
        return result

    def request_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_request, user_id, pkg_id, org_id)

    def approve_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_approve, user_id, pkg_id, org_id)

    def assign_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_assign, user_id, pkg_id, org_id)

    @property
    def id(self):
        return (self.from_state, self.to_state)
