
import logging
import requests
import urllib2

from ckan.lib.helpers import json
from ckan.plugins.core import SingletonPlugin

from ckanext.datitrentinoit.model.statweb_metadata import StatWebProIndex, StatWebProEntry, StatWebMetadataPro
import ckanext.datitrentinoit.model.mapping as mapping

from ckanext.datitrentinoit.harvesters.statwebbase import StatWebBaseHarvester

log = logging.getLogger(__name__)


class StatWebProHarvester(StatWebBaseHarvester, SingletonPlugin):
    '''
    Harvester per StatWeb Pro

    GATHER: fa richiesta al servizio indice e salva ogni entry in un HarvestObject
    FETCH:  legge l'HarvestObject, fa il retrieve dei metadati, aggiorna il contenuto dell'HarvestObject 
            aggiungendo i metadati appena caricati
    IMPORT: effettua il parsing dell'HarvestObject e crea/aggiorna il dataset corrispondente
    '''

    def info(self):
        return {
            'name': 'tn_statweb_pro',
            'title': 'StatWebPro',
            'description': 'Harvester per servizio StatWebPro',
            'form_config_interface': 'Text'
        }

    def harvester_name(self):
        return 'StatWebPro'

    ## IHarvester

    def validate_config(self, source_config):
        if not source_config:
            return source_config

        try:
            source_config_obj = json.loads(source_config)

            if 'groups' in source_config_obj:
                if not isinstance(source_config_obj['groups'], list):
                    raise ValueError('"groups" should be a list')

        except ValueError as e:
            raise e

        return source_config

    def create_index(self, url):
        log.info('%s: connecting to %s', self.harvester_name(), url)
        request = urllib2.Request(url)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(), urllib2.HTTPRedirectHandler())

        response = opener.open(request)
        content = response.read()

        return StatWebProIndex(content)

    def create_package_dict(self, guid, content):
        swpentry = StatWebProEntry(str=content)
        metadata = StatWebMetadataPro(obj=swpentry.get_metadata())
        orig_id = swpentry.get_id()
        package_dict = mapping.create_pro_package_dict(guid, orig_id, metadata, self.source_config)
        return package_dict, metadata

    def fetch_stage(self, harvest_object):

        # Check harvest object status
        status = self._get_object_extra(harvest_object, 'status')

        if status == 'delete':
            # No need to fetch anything, just pass to the import stage
            return True

        log = logging.getLogger(__name__ + '.fetch')
        log.debug('StatWebPro fetch_stage for object: %s', harvest_object.id)

        entry = StatWebProEntry(str=harvest_object.content)
        url = entry.get_url()
        identifier = harvest_object.guid

        log.info('Retrieving StatWebPro metadata from %s', url)

        content = None;
        
        try:
            request = urllib2.Request(url)
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(), urllib2.HTTPRedirectHandler())
            response = opener.open(request)
            content = response.read()
        except Exception, e:
            self._save_object_error('Error getting the StatWebPro record with GUID %s' % identifier, harvest_object)
            return False

        if content is None:
            self._save_object_error('Empty record for GUID %s' % identifier, harvest_object)
            return False

        metadata = StatWebMetadataPro(str=content)
        entry.set_metadata(metadata.get_obj())

        # Update the harvest_object content, adding the metadata
        try:
            harvest_object.content = entry.tostring()
            harvest_object.save()
        except Exception,e:
            self._save_object_error('Error saving the harvest object for GUID %s [%r]' % \
                                    (identifier, e), harvest_object)
            return False

        return True


    def attach_resources(self, metadata, package_dict):

        for resource_key in ["Indicatore", "TabNumeratore", "TabDenominatore"]:
            json_resource_url = metadata.get(resource_key)
            if not json_resource_url:
                continue

            log.debug('StatWebPro: loading resource %s', resource_key)

            rdata = requests.get(json_resource_url)
            if not rdata.ok:
                log.info('StatWebPro error loading %s for guid %s', json_resource_url, harvest_object.guid)
                continue
            else:
                log.debug('StatWebPro: loaded resource %s', resource_key)

            res_title = rdata.json().keys()[0]

            res_dict_json = {
                'name': res_title,
                'description': res_title,
                'url': json_resource_url,
                'format': 'json',
                'mimetype': 'application/json',
                'resource_type': 'api',
#                'last_modified': modified,
            }
            package_dict['resources'].append(res_dict_json)

            # Get also the twin CSV resource
            csv_resource_url = metadata.get(resource_key + "CSV")
            if not csv_resource_url:
                continue

            res_dict_csv = {
                'name': res_title,
                'description': res_title,
                'url': csv_resource_url,
                'format': 'csv',
                'mimetype': 'text/csv',
                'resource_type': 'file',
#                'last_modified': modified,
            }
            package_dict['resources'].append(res_dict_csv)
            
