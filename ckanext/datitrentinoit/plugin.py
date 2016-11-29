
import ckan.plugins as plugins
import logging

import ckan.lib.base as base
import ckan.plugins.toolkit as plugins_toolkit
import routes.mapper as routes_mapper

import ckanext.datitrentinoit.helpers as helpers

import ckanext.datitrentinoit.model.custom as custom

import ckanext.dcatapit.interfaces as interfaces

from ckan.common import _, ungettext

log = logging.getLogger(__name__)

static_pages = ['faq', 'acknowledgements', 'legal_notes', 'privacy']

class DatiTrentinoPlugin(plugins.SingletonPlugin):

    """Controller used to load custom templates/resources/pages"""

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(interfaces.ICustomSchema)

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
                'localized': True
            }, {
                'name': 'contact',
                'validator': ['ignore_missing'],
                'element': 'input',
                'type': 'email',
                'label': _('Contact'),
                'placeholder': _('contact'),
                'is_required': False,
                'localized': True
            }, {
                'name': 'fields_description',
                'validator': ['ignore_missing'],
                'element': 'textarea',
                'label': _('Fields Description'),
                'placeholder': _('description of the dataset fields'),
                'is_required': False,
                'localized': True
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
            'dti_get_localized_field_value': helpers.getLocalizedFieldValue,
            'dti_get_language': helpers.getLanguage
        }

    def _get_ga_site_id(self):
        return self.ga_conf['id']

    def _get_ga_site_domain(self):
        return self.ga_conf['domain']

    def after_create(self, context, pkg_dict):
        # During the harvest the get_lang() is not defined
        lang = helpers.getLanguage()

        if lang:    
            for extra in pkg_dict.get('extras'):
                for field in self.get_custom_schema():
                    if extra.get('key') == field['name'] and field['localized'] == True:
                        log.info(':::::::::::::::Localizing custom field: %r', field['name'])
                        
                        # Create the localized field record
                        self.createLocField(extra, lang, pkg_dict.get('id'))

    def after_update(self, context, pkg_dict):
        # During the harvest the get_lang() is not defined
        lang = helpers.getLanguage()

        if lang:             
            for extra in pkg_dict.get('extras'):
                for field in self.get_custom_schema():
                    if extra.get('key') == field['name'] and field['localized'] == True:
                        log.info(':::::::::::::::Localizing custom field: %r', field['name'])
                        f = custom.get_field(extra.get('key'), pkg_dict.get('id'), lang)
                        if f:
                            if extra.get('value') == '':
                                f.purge()
                            elif f.text != extra.get('value'):
                                # Update the localized field value for the current language
                                f.text = extra.get('value')
                                f.save()

                                log.info('Custom field updated successfully')

                        elif extra.get('value') != '':
                            # Create the localized field record
                            self.createLocField(extra, lang, pkg_dict.get('id'))

    def createLocField(self, extra, lang, package_id): 
        log.debug('Creating createLocField for package ID: %r', str(package_id))

        new_loc_field = custom.CustomFieldMultilang(package_id, extra.get('key'), lang, extra.get('value'))
        custom.CustomFieldMultilang.save(new_loc_field)

        log.info('Custom field created successfully')

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
