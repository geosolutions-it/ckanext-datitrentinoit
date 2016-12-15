
import hashlib
import logging
import uuid

from pylons import config

from ckan import logic
from ckan import model
from ckan import plugins as p
from ckan.model import Session

from ckan.plugins.core import SingletonPlugin, implements

from ckanext.harvest.interfaces import IHarvester
from ckanext.harvest.harvesters.base import HarvesterBase
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.model import HarvestObjectExtra as HOExtra

from ckan.lib.search.index import PackageSearchIndex
from ckan.lib.helpers import json
from ckan.lib.navl.validators import not_empty

log = logging.getLogger(__name__)


class StatWebBaseHarvester(HarvesterBase, SingletonPlugin):
    '''
    Harvester per StatWeb Pro

    GATHER: fa richiesta al servizio indice e salva ogni entry in un HarvestObject
    FETCH:  legge l'HarvestObject, fa il retrieve dei metadati, aggiorna il contenuto dell'HarvestObject 
            aggiungendo i metadati appena caricati
    IMPORT: effettua il parsing dell'HarvestObject e crea/aggiorna il dataset corrispondente
    '''

    implements(IHarvester)

    _user_name = None

    source_config = {}

    def harvester_name(self):
        raise NotImplementedError

    def create_index(self, url):
        """
        return an object exposing the methods:
        - keys(): return all the keys of the harvested documents
        - index.get_as_string(key): return the document entry related to a key
        """
        raise NotImplementedError

    def create_package_dict(self, guid, content):
        raise NotImplementedError

    def attach_resources(self, metadata, package_dict):
        raise NotImplementedError

    def info(self):
        raise NotImplementedError

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

    def gather_stage(self, harvest_job):
        log = logging.getLogger(__name__ + '.gather')
        log.debug('%s gather_stage for job: %r', self.harvester_name(), harvest_job)
        # Get source URL
        url = harvest_job.source.url

        self._set_source_config(harvest_job.source.config)

        try:
            index = self.create_index(url)
        except Exception as e:
            self._save_gather_error('Error harvesting %s: %s' % (self.harvester_name(), e), harvest_job)
            return None


        query = model.Session.query(HarvestObject.guid, HarvestObject.package_id).\
                                    filter(HarvestObject.current == True).\
                                    filter(HarvestObject.harvest_source_id == harvest_job.source.id)
        guid_to_package_id = {}

        for guid, package_id in query:
            guid_to_package_id[guid] = package_id

        guids_in_db = set(guid_to_package_id.keys())

        #log.debug('Starting gathering for %s' % url)
        guids_in_harvest = index.keys()

        new = guids_in_harvest - guids_in_db
        delete = guids_in_db - guids_in_harvest
        change = guids_in_db & guids_in_harvest

        ids = []
        for guid in new:
            doc = index.get_as_string(guid)
            obj = HarvestObject(guid=guid, job=harvest_job, content=doc,
                                extras=[HOExtra(key='status', value='new')])
            obj.save()
            ids.append(obj.id)

        for guid in change:
            doc = index.get_as_string(guid)
            obj = HarvestObject(guid=guid, job=harvest_job, content=doc,
                                package_id=guid_to_package_id[guid],
                                extras=[HOExtra(key='status', value='change')])
            obj.save()
            ids.append(obj.id)

        for guid in delete:
            obj = HarvestObject(guid=guid, job=harvest_job,
                                package_id=guid_to_package_id[guid],
                                extras=[HOExtra(key='status', value='delete')])
            ids.append(obj.id)
            model.Session.query(HarvestObject).\
                  filter_by(guid=guid).\
                  update({'current': False}, False)
            obj.save()

        if len(ids) == 0:
            self._save_gather_error('No records received from the %s service' % self.harvester_name(), harvest_job)
            return None

        return ids


    def fetch_stage(self, harvest_object):
        return True

    def import_stage(self, harvest_object):

        log = logging.getLogger(__name__ + '.import')
        log.debug('%s: Import stage for harvest object: %s', self.harvester_name(), harvest_object.id)

        if not harvest_object:
            log.error('No harvest object received')
            return False

        if not harvest_object.content:
            log.error('Harvest object contentless')
            self._save_object_error(
                'Empty content for object %s' % harvest_object.id,
                harvest_object,
                'Import'
            )
            return False

        self._set_source_config(harvest_object.source.config)

        status = self._get_object_extra(harvest_object, 'status')

        # Get the last harvested object (if any)
        previous_object = Session.query(HarvestObject) \
                          .filter(HarvestObject.guid == harvest_object.guid) \
                          .filter(HarvestObject.current == True) \
                          .first()

        context = {'model': model, 'session': model.Session, 'user': self._get_user_name()}

        if status == 'delete':
            # Delete package
            p.toolkit.get_action('package_delete')(context, {'id': harvest_object.package_id})
            log.info('Deleted package {0} with guid {1}'.format(harvest_object.package_id, harvest_object.guid))

            return True

        # Flag previous object as not current anymore
        if previous_object:
            previous_object.current = False
            previous_object.add()

        # Flag this object as the current one
        harvest_object.current = True
        harvest_object.add()
        
        # Generate GUID if not present (i.e. it's a manual import)
        if not harvest_object.guid:
            self._save_object_error('Missing GUID for object {0}'
                        .format(harvest_object.id), harvest_object, 'Import')
            return False

        # pre-check to skip resource logic in case no changes occurred remotely
        if status == 'change':

            # Check if the document has changed
            m = hashlib.md5()
            m.update(previous_object.content)
            old_md5 = m.hexdigest()

            m = hashlib.md5()
            m.update(harvest_object.content)
            new_md5 = m.hexdigest()

            if old_md5 == new_md5:

                # Assign the previous job id to the new object to # avoid losing history
                harvest_object.harvest_job_id = previous_object.job.id
                harvest_object.add()

                harvest_object.metadata_modified_date = previous_object.metadata_modified_date
                harvest_object.add()

                # Delete the previous object to avoid cluttering the object table
                previous_object.delete()

                # Reindex the corresponding package to update the reference to the harvest object
                context.update({'validate': False, 'ignore_auth': True})
                try:
                    package_dict = logic.get_action('package_show')(context,
                        {'id': harvest_object.package_id})
                except p.toolkit.ObjectNotFound:
                    pass
                else:
                    for extra in package_dict.get('extras', []):
                        if extra['key'] == 'harvest_object_id':
                            extra['value'] = harvest_object.id
                    if package_dict:
                        package_index = PackageSearchIndex()
                        package_index.index_package(package_dict)

                log.info('%s document with GUID %s unchanged, skipping...', self.harvester_name(),harvest_object.guid)
                model.Session.commit()

                return True


        # Build the package dict
        package_dict, metadata = self.create_package_dict(harvest_object.guid, harvest_object.content)

        if not package_dict:
            log.error('No package dict returned, aborting import for object {0}'.format(harvest_object.id))
            return False

        package_dict['name'] = self._gen_new_name(package_dict['title'])

        # We need to get the owner organization (if any) from the harvest source dataset
        source_dataset = model.Package.get(harvest_object.source.id)
        if source_dataset.owner_org:
            package_dict['owner_org'] = source_dataset.owner_org

        self.attach_resources(metadata, package_dict)

        # Create / update the package

        context = {'model': model,
                   'session': model.Session,
                   'user': self._get_user_name(),
                   'extras_as_string': True,
                   'api_version': '2',
                   'return_id_only': True}
        if context['user'] == self._site_user['name']:
            context['ignore_auth'] = True

        # The default package schema does not like Upper case tags
        tag_schema = logic.schema.default_tags_schema()
        tag_schema['name'] = [not_empty, unicode]

        if status == 'new':
            package_schema = logic.schema.default_create_package_schema()
            package_schema['tags'] = tag_schema
            context['schema'] = package_schema

            # We need to explicitly provide a package ID, otherwise ckanext-spatial
            # won't be be able to link the extent to the package.
            package_dict['id'] = unicode(uuid.uuid4())
            package_schema['id'] = [unicode]

            # Save reference to the package on the object
            harvest_object.package_id = package_dict['id']
            harvest_object.add()
            # Defer constraints and flush so the dataset can be indexed with
            # the harvest object id (on the after_show hook from the harvester
            # plugin)
            Session.execute('SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
            model.Session.flush()

            try:
                package_id = p.toolkit.get_action('package_create')(context, package_dict)
                log.info('%s: Created new package %s with guid %s', self.harvester_name(), package_id, harvest_object.guid)
            except p.toolkit.ValidationError as e:
                self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                return False

        elif status == 'change':
            # we know the internal document did change, bc of a md5 hash comparison done above

            package_schema = logic.schema.default_update_package_schema()
            package_schema['tags'] = tag_schema
            context['schema'] = package_schema

            package_dict['id'] = harvest_object.package_id
            try:
                package_id = p.toolkit.get_action('package_update')(context, package_dict)
                log.info('%s updated package %s with guid %s', self.harvester_name(), package_id, harvest_object.guid)
            except p.toolkit.ValidationError as e:
                self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                return False

        model.Session.commit()

        return True
            

    def _set_source_config(self, config_str):
        '''
        Loads the source configuration JSON object into a dict for
        convenient access
        '''
        if config_str:
            self.source_config = json.loads(config_str)
            log.debug('%s Using config: %r', self.harvester_name(), self.source_config)
        else:
            self.source_config = {}

    def _get_object_extra(self, harvest_object, key):
        '''
        Helper function for retrieving the value from a harvest object extra,
        given the key
        '''
        for extra in harvest_object.extras:
            if extra.key == key:
                return extra.value
        return None

    def _get_user_name(self):
        '''
        Returns the name of the user that will perform the harvesting actions
        (deleting, updating and creating datasets)

        By default this will be the internal site admin user. This is the
        recommended setting, but if necessary it can be overridden with the
        `ckanext.spatial.harvest.user_name` config option, eg to support the
        old hardcoded 'harvest' user:

           ckanext.spatial.harvest.user_name = harvest

        '''
        if self._user_name:
            return self._user_name

        self._site_user = p.toolkit.get_action('get_site_user')({'model': model, 'ignore_auth': True}, {})

        config_user_name = config.get('ckanext.spatial.harvest.user_name')
        if config_user_name:
            self._user_name = config_user_name
        else:
            self._user_name = self._site_user['name']

        return self._user_name
