
import ckan.plugins as plugins
import logging

import ckan.lib.base as base
import ckan.plugins.toolkit as plugins_toolkit
import routes.mapper as routes_mapper

import ckanext.datitrentinoit.helpers as helpers

import ckanext.dcatapit.interfaces as interfaces

from ckan.common import _, ungettext

try:
    from ckan.lib.plugins import DefaultTranslation
except ImportError:
    class DefaultTranslation():
        pass

log = logging.getLogger(__name__)

static_pages = ['faq', 'acknowledgements', 'legal_notes', 'privacy']

class DatiTrentinoPlugin(plugins.SingletonPlugin, DefaultTranslation):

    # IConfigurer
    plugins.implements(plugins.IConfigurer)

    # IConfigurable
    plugins.implements(plugins.IConfigurable)

    # ITemplateHelpers
    plugins.implements(plugins.ITemplateHelpers)

    # IRoutes
    plugins.implements(plugins.IRoutes)

    # IPackageController
    plugins.implements(plugins.IPackageController, inherit=True)

    # ICustomSchema
    plugins.implements(interfaces.ICustomSchema)

    # ITranslation
    if plugins_toolkit.check_ckan_version(min_version='2.5.0'):
        plugins.implements(plugins.ITranslation, inherit=True)

    # Implementation of ICustomSchema
    # ------------------------------------------------------------

    def get_custom_schema(self):
        return [
            {
                'name': 'creation_date',
                'validator': ['ignore_missing'],
                'element': 'input',
                'type': 'date',
                'label': _('Creation Date'),
                'format': '%d-%m-%Y',
                'placeholder': _('creation date'),
                'is_required': False,
                'localized': False
            },  {
                'name': 'encoding',
                'validator': ['ignore_missing'],
                'element': 'input',
                'type': 'text',
                'label': _('Encoding'),
                'placeholder': _('encoding type'),
                'is_required': False,
                'localized': False
            }, {
                'name': 'site_url',
                'validator': ['ignore_missing'],
                'element': 'input',
                'type': 'url',
                'label': _('Site URL'),
                'placeholder': _('site url'),
                'is_required': False,
                'localized': False
            }, {
                'name': 'contact',
                'validator': ['ignore_missing'],
                'element': 'input',
                'type': 'email',
                'label': _('Contact'),
                'placeholder': _('contact'),
                'is_required': False,
                'localized': False,
                'ignore_from_info': True
            }, {
                'name': 'fields_description',
                'validator': ['ignore_missing'],
                'element': 'textarea',
                'label': _('Fields Description'),
                'placeholder': _('description of the dataset fields'),
                'is_required': False,
                'localized': True,
                'ignore_from_info': True
            }
        ]

    # Implementation of IConfigurer
    # ------------------------------------------------------------

    def update_config(self, config):
        plugins_toolkit.add_public_directory(config, 'public')
        plugins_toolkit.add_template_directory(config, 'templates')
        plugins_toolkit.add_resource('fanstatic', 'ckanext-datitrentinoit')

    # Implementation of IConfigurable
    # ------------------------------------------------------------

    def configure(self, config):
        self.ga_conf = {
            'id': config.get('googleanalytics.id'),
            'domain': config.get('googleanalytics.domain'),
        }

    # Implementation of IRoutes
    # ------------------------------------------------------------

    def before_map(self, routes):
        controller = 'ckanext.datitrentinoit.plugin:DatiTrentinoController'
        with routes_mapper.SubMapper(routes, controller=controller) as m:
            for page_name in static_pages:
                page_slug = page_name.replace('_', '-')
                m.connect(page_name, '/' + page_slug, action=page_name)
        return routes

    def after_map(self, routes):
        return routes

    # Implementation of ITemplateHelpers
    # ------------------------------------------------------------

    def get_helpers(self):
        return {
            'dti_ga_site_id': self._get_ga_site_id,
            'dti_ga_site_domain': self._get_ga_site_domain,
            'dti_recent_updates': helpers.recent_updates,
            'hacked_current_url': helpers.hacked_current_url,
        }

    def _get_ga_site_id(self):
        return self.ga_conf['id']

    def _get_ga_site_domain(self):
        return self.ga_conf['domain']


class DatiTrentinoController(base.BaseController):
    """Controller used to add custom pages"""

for page_name in static_pages:
    def get_action(name):
        def action(self):
            return base.render('pages/{0}.html'.format(name))
        return action
    action = get_action(page_name)
    action.__name__ = page_name
    setattr(DatiTrentinoController, page_name, action)
