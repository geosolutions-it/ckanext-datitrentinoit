# Ckan plugin for dati.trentino.it

[CKAN] Extension for the Provincia di Trento (http://dati.trentino.it)

[Ckan]: http://ckan.org

## Plugins

Available plugins in this extension:

- ``datitrentinoit``: Theme customization
- ``statwebpro_harvester``: harvests metadata at level "**pro**" from services exposed by http://www.statweb.provincia.tn.it/.
- ``statwebsubpro_harvester``: harvests metadata at level "**subpro**" from services exposed by http://www.statweb.provincia.tn.it/.
- ``csw_tn_harvester``: harvests CSW metadata bypassing the *GetRecordById* validation: the ``gmd:MD_Metadata`` element returned by the service http://www.territorio.provincia.tn.it/geoportlet/srv/eng/csw is not included in an element ``csw:GetRecordByIdResponse``.

## Requirements

The ckanext-dcatapit extension has been developed for CKAN 2.5.2 or later.
This extension requires the following extensions: ``ckanext-harvester``, ``ckanext-spatial``, ``ckanext-geonetwork``, ``ckanext-multilang`` e ``ckanext-dcatapit``.

## Installation

1. Installing all the other required extensions

2. Activate your CKAN virtual environment, for example:

     `. /usr/lib/ckan/default/bin/activate`
     
3. Go into your CKAN path for extension (like /usr/lib/ckan/default/src):

    `git clone https://github.com/geosolutions-it/ckanext-datitrentinoit.git`
    
    `cd ckanext-datitrentinoit`
    
    `pip install -e .`

4. Add ``datitrentinoit``, ``statwebpro_harvester``, ``statwebsubpro_harvester`` and ``csw_tn_harvester`` to the ``ckan.plugins`` setting in your CKAN config file (by default the config file is located at ``/etc/ckan/default/production.ini``).

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload

## Development Installation

To install `ckanext-datitrentinoit` for development, activate your CKAN virtualenv and do:

    git clone https://github.com/geosolutions-it/ckanext-datitrentinoit.git
    
    cd ckanext-datitrentinoit
    
    python setup.py develop

    pip install -r dev-requirements.txt

## CSW Harvest Configuration

Using the ckanext-datitrentinoit harvester you can use an additional configuration property in addition to the other allowed for the ckanext-geonetwork and ckanext-multilang harvesters:

* ``default_license``: with this property you can specify the default license to use for the CKAN's dataset if none useLimitation has been found into the metadata. Below an example:

        {
            "default_license": "cc-zero"
        }
	
* ``default_values``: with this property you can specify some default values to use for missing properties in CSW metadata. Default values are defined into the harvester but can be overridden in the CKAN harvest source json configuration. Below the predefined defaults:

		{
			'dataset_theme': 'OP_DATPRO',
			'dataset_place': 'ITA_TRT',
			'dataset_language': '{ITA,DEU,ENG}',
			'agent_code': 'p_TN',
			'frequency': 'UNKNOWN',
			'agent_code_regex': {
			    'regex': '\(([^)]+)\:([^)]+)\)',
			    'groups': [2] # optional, dependes by the regular expression
			},
			'org_name_regex': {
			    'regex': '([^(]*)(\(IPa[^)]*\))(.+)',
			    'groups': [1,3] # optional, dependes by the regular expression
			},
			'dcatapit_skos_theme_id': 'theme.data-theme-skos',
			'dcatapit_skos_places_id': 'theme.places-skos'
		}
	
	**note**:
		the **agent_code_regex** and **org_name_regex** (regex and/or group properties) must be changed if the corresponding 'organizationName'
		value change in the CSW metadata. Current default value has been set to match a string type like the following:

		Provincia Autonoma di Bolzano (IPa: p_bz) - Ripartizione 28 - Natura, paesaggio e sviluppo del territorio
		
	where the **agent_code_regex** match the IPa code **p_bz** and the **org_name_regex** match the organization name
	value **Provincia Autonoma di Bolzano - Ripartizione 28 - Natura, paesaggio e sviluppo del territorio**.
	
	the **dcatapit_skos_theme_id** and **dcatapit_skos_places_id** values correspond to the thesaurus identifiers speficied in the CSW metadata (related to the eu_theme.rdf and places.rdf themes) so if the metadata values change also these configuration options must be modified accordingly. 

Below an example of configuration that shows all the available properties:

        {
			"private_datasets": "False", 
			"version": "2.6",
	        "default_values": {
			    'dataset_theme': 'OP_DATPRO',
			    'dataset_place': 'ITA_TRT',
			    'dataset_language': '{ITA,DEU,ENG}',
			    'agent_code': 'p_TN',
			    'frequency': 'UNKNOWN',
			    'agent_code_regex': {
					'regex': '\(([^)]+)\:([^)]+)\)',
					'groups': [2] # optional, dependes by the regular expression
			    },
			    'org_name_regex': {
					'regex': '([^(]*)(\(IPa[^)]*\))(.+)',
					'groups': [1,3] # optional, dependes by the regular expression
			    },
			    'dcatapit_skos_theme_id': 'theme.data-theme-skos',
			    'dcatapit_skos_places_id': 'theme.places-skos'
	        },
			"harvest_iso_categories": "True",
			"organisation_mapping": [
				{
					"key": "nome-org-1",
					"value": "organization-name-of-responsible-party-with-role-owner-1",
					"value_it":"it-localized-org-name-1",
					"value_de":"de-localized-org-name-1"
				},
				{
					"key": "nome-org-2",
					"value": "organization-name-of-responsible-party-with-role-owner-2",
					"value_it":"it-localized-org-name-2",
					"value_de":"de-localized-org-name-2"
				}
			],
			"group_mapping": {
				"farming": "ckan-group-1", 
				"utilitiesCommunication": "ckan-group-1", 
				"transportation": "ckan-group-1", 
				"inlandWaters": "ckan-group-2", 
				"geoscientificInformation": "ckan-group-1", 
				"environment": "ckan-group-2", 
				"climatologyMeteorologyAtmosphere": "ckan-group-1", 
				"planningCadastre": "ckan-group-1", 
				"imageryBaseMapsEarthCover": "ckan-group-3", 
				"elevation": "ckan-group-4", 
				"boundaries": "ckan-group-5",
				"structure": "ckan-group-6", 
				"location": "ckan-group-7", 
				"economy": "ckan-group-1",
				"society": "ckan-group-2",
				"biota": "ckan-group-2",
				"intelligenceMilitary": "ckan-group-1",
				"oceans": "ckan-group-4",
				"health": "ckan-group-5"
			},
			"ckan_locales_mapping":{
				"ita": "it",
				"ger": "de"
			},
			"default_license": "cc-zero"
		}

## Managing translations

The datitrentinoit extension implements the ITranslation CKAN's interface so the translations procedure of the GUI elements is automatically covered using the translations files provided in the i18n directory. 

### Creating a new translation

To create a new translation proceed as follow:

1. Extract new messages from your extension updating the pot file:

     `python setup.py extract_messages`
     
2.  Create a translation file for your language (a po file) using the existing pot file in this plugin:

     `python setup.py init_catalog --locale YOUR_LANGUAGE`

     Replace YOUR_LANGUAGE with the two-letter ISO language code (e.g. es, de).
     
3. Do the translation into the po file

4. Once the translation files (po) have been updated, either manually or via Transifex, compile them by running::

     `python setup.py compile_catalog --locale YOUR_LANGUAGE`
     
### Updating an existing translation

In order to update the existing translations proceed as follow:

1. Extract new messages from your extension updating the pot file:

     `python setup.py extract_messages`
     
2. Update the strings in your po file, while preserving your po edits, by doing:

     `python setup.py update_catalog --locale YOUR-LANGUAGE`

3. Once the translation files (po) have been updated adding the new translations needed, compile them by running:

     `python setup.py compile_catalog --locale YOUR_LANGUAGE`

## Using custom licenses.

Customized dataset license list is available in `ckanext/datitrentinoit/licenses/licenses.json`. To use it, set `licenses_group_url` config 
var to `https://github.com/geosolutions-it/ckanext-datitrentinoit/tree/dcatapit/ckanext/datitrentinoit/licenses/licenses.json`.
