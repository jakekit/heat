#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from glanceclient import client as gc
from glanceclient import exc
from glanceclient.openstack.common.apiclient import exceptions

from heat.engine.clients import client_plugin
from heat.engine import constraints

CLIENT_NAME = 'glance'


class GlanceClientPlugin(client_plugin.ClientPlugin):

    exceptions_module = [exceptions, exc]

    service_types = [IMAGE] = ['image']

    def _create(self):

        con = self.context
        endpoint_type = self._get_client_option(CLIENT_NAME, 'endpoint_type')
        endpoint = self.url_for(service_type=self.IMAGE,
                                endpoint_type=endpoint_type)
        args = {
            'auth_url': con.auth_url,
            'service_type': self.IMAGE,
            'project_id': con.tenant_id,
            'token': self.auth_token,
            'endpoint_type': endpoint_type,
            'cacert': self._get_client_option(CLIENT_NAME, 'ca_file'),
            'cert_file': self._get_client_option(CLIENT_NAME, 'cert_file'),
            'key_file': self._get_client_option(CLIENT_NAME, 'key_file'),
            'insecure': self._get_client_option(CLIENT_NAME, 'insecure')
        }

        return gc.Client('1', endpoint, **args)

    def _find_with_attr(self, entity, **kwargs):
        """Find a item for entity with attributes matching ``**kwargs``."""
        matches = list(self._findall_with_attr(entity, **kwargs))
        num_matches = len(matches)
        if num_matches == 0:
            msg = ("No %(name)s matching %(args)s.") % {
                'name': entity,
                'args': kwargs
            }
            raise exceptions.NotFound(msg)
        elif num_matches > 1:
            raise exceptions.NoUniqueMatch()
        else:
            return matches[0]

    def _findall_with_attr(self, entity, **kwargs):
        """Find all items for entity with attributes matching ``**kwargs``."""
        func = getattr(self.client(), entity)
        filters = {'filters': kwargs}
        return func.list(**filters)

    def is_not_found(self, ex):
        return isinstance(ex, (exceptions.NotFound, exc.HTTPNotFound))

    def is_over_limit(self, ex):
        return isinstance(ex, exc.HTTPOverLimit)

    def is_conflict(self, ex):
        return isinstance(ex, (exceptions.Conflict, exc.Conflict))

    def find_image_by_name_or_id(self, image_identifier):
        """Return the ID for the specified image name or identifier.

        :param image_identifier: image name or a UUID-like identifier
        :returns: the id of the requested :image_identifier:
        """
        try:
            return self.client().images.get(image_identifier).id
        except exc.HTTPNotFound:
            return self._find_with_attr('images', name=image_identifier).id


class ImageConstraint(constraints.BaseCustomConstraint):
    expected_exceptions = (exceptions.NotFound, exceptions.NoUniqueMatch)

    resource_client_name = CLIENT_NAME
    resource_getter_name = 'find_image_by_name_or_id'
