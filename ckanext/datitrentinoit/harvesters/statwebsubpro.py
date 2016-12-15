
import logging
import requests
import urllib2

from ckan.lib.helpers import json
from ckan.plugins.core import SingletonPlugin

from ckanext.datitrentinoit.model.statweb_metadata import StatWebSubProIndex, StatWebMetadataSubPro, SubProMetadata
import ckanext.datitrentinoit.model.mapping as mapping

from ckanext.datitrentinoit.harvesters.statwebbase import StatWebBaseHarvester


log = logging.getLogger(__name__)


class StatWebSubProHarvester(StatWebBaseHarvester, SingletonPlugin):
    '''
    Harvester per StatWeb SubPro

    GATHER: fa richiesta al servizio indice e salva ogni entry in un HarvestObject.
            L'indice comprende anche i metadati del dataset
    FETCH:  Non fa nulla: i metadati sono caricati dall'indice nella fase di GATHER
    IMPORT: effettua il parsing dell'HarvestObject e crea/aggiorna il dataset corrispondente.
    '''

    def info(self):
        return {
            'name': 'tn_statweb_subpro',
            'title': 'StatWebSubPro',
            'description': 'Harvester per servizio StatWeb SubPro',
            'form_config_interface': 'Text'
        }

    def harvester_name(self):
        return 'StatWebSubPro'

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

        return StatWebSubProIndex(content)

    def create_package_dict(self, guid, content):
        metadata = StatWebMetadataSubPro(str=content)
        package_dict = mapping.create_subpro_package_dict(guid, metadata, self.source_config)
        return package_dict, metadata

    def fetch_stage(self, harvest_object):
        return True


    def attach_resources(self, metadata, package_dict):

        for resource_key in ["URLIndicatore"]:
            json_resource_url = metadata.get(resource_key)
            if not json_resource_url:
                continue

            self._attach_data_resources(json_resource_url, package_dict)

        for md_resource_key in ["URLTabDenMD", "URLTabNumMD"]:
            md_resource_url = metadata.get(md_resource_key)
            if not md_resource_url:
                continue

            log.debug('Attaching MD resources to "%s"', metadata.get_descrizione() )
            self._attach_md_resources(md_resource_url, package_dict)


    def _attach_md_resources(self, md_resource_url, package_dict):
        rmd = requests.get(md_resource_url)
        if not rmd.ok:
            log.warn('StatWebSubPro error loading resource metadata %s for guid %s', md_resource_url, harvest_object.guid)
            return

        if not rmd.content:
            log.warn('Empty json at resource URL %s', md_resource_url)
            return

        try:
            spmd = SubProMetadata(str=rmd.content)
            log.debug('Attaching resource "%s"', spmd.get_descrizione())
            self._attach_data_resources(spmd.get_data_url(), package_dict)
        except ValueError as e:
            log.warn('Error decoding json\n URL: %s\njson: "%s"', rmd.content)


    def _attach_data_resources(self, json_resource_url, package_dict):
        """
        Attach the JSON resource and the related CSV resource
        """

        rdata = requests.get(json_resource_url)
        if not rdata.ok:
            log.warn('StatWebSubPro error loading json resource at %s', json_resource_url)
            return

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
        csv_resource_url = json_resource_url.replace("fmt=json", "fmt=csv")

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
            
