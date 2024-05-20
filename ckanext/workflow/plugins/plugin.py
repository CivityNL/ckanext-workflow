# encoding: utf-8

'''Constants.'''

import os
import ckanext.workflow.common as common
from ckanext.authorization.interface import IAuthorization

log = common.getLogger(__name__)


class WorkflowPlugin(common.SingletonPlugin, common.DefaultTranslation):
    common.implements(common.ITranslation)
    common.implements(common.IConfigurable)
    common.implements(common.IConfigurer)
    common.implements(IAuthorization, inherit=True)

    # ITranslation
    def i18n_directory(self):
        path = os.path.abspath(
            os.path.join(
                super(WorkflowPlugin, self).i18n_directory(), "..", "..", "i18n"
            )
        )
        return path

    # IConfigurable
    def configure(self, config):
        pass


    # IConfigurer
    def update_config(self, config):
        common.add_template_directory(config, '../templates')


    # IAuthorization
    def get_group_capacities(self, capacities):
        capacities.update(
            {
                'banana': {
                    'permissions': capacities['editor']['permissions'],
                    'description': {'en': "I'm yellow", 'nl': 'Ik ben geel'},
                    'label': {'en': "Banana", 'nl': 'Banaan'}
                }
            }
        )
        return capacities

    def get_dataset_capacities(self, capacities):
        capacities.update(
            {
                'apple': {
                    'permissions': capacities['editor']['permissions'],
                    'description': {'en': "I'm round and juicy", 'nl': 'Ik ben rond and sappig'},
                    'label': {'en': "Apple", 'nl': 'Appel'}
                }
            }
        )
        return capacities
