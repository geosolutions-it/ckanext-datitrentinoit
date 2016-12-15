# Ckan plugin for dati.trentino.it

[CKAN] Extension for the Provincia di Trento (http://dati.trentino.it)

[Ckan]: http://ckan.org

-------
Plugins
-------

Available plugins in this extension:

- ``datitrentinoit``: Theme customization
- ``statwebpro_harvester``: harvests metadata at level "**pro**" from services exposed by http://www.statweb.provincia.tn.it/.
- ``statwebsubpro_harvester``: harvests metadata at level "**subpro**" from services exposed by http://www.statweb.provincia.tn.it/.
- ``csw_tn_harvester``: harvests CSW metadata bypassing the *GetRecordById* validation: the ``gmd:MD_Metadata`` element returned by the service http://www.territorio.provincia.tn.it/geoportlet/srv/eng/csw is not included in an element ``csw:GetRecordByIdResponse``.


------------
Requirements
------------

The ckanext-dcatapit extension has been developed for CKAN 2.5.2 or later.
This extension requires the following extensions: ``ckanext-harvester``, ``ckanext-spatial``, ``ckanext-multilang`` e ``ckanext-dcatapit``.

------------
Installation
------------

1. Installing all the other extensions required

2. Activate your CKAN virtual environment, for example::

     `. /usr/lib/ckan/default/bin/activate`
     
3. Go into your CKAN path for extension (like /usr/lib/ckan/default/src)::

    `git clone https://github.com/geosolutions-it/ckanext-datitrentinoit.git`
    
    `cd ckanext-datitrentinoit`
    
    `pip install -e .`

4. Add ``datitrentinoit``, ``statwebpro_harvester``, ``statwebsubpro_harvester`` and ``csw_tn_harvester`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at ``/etc/ckan/default/production.ini``).

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


------------------------
Development Installation
------------------------

To install `ckanext-datitrentinoit` for development, activate your CKAN virtualenv and
do::

    `git clone https://github.com/geosolutions-it/ckanext-datitrentinoit.git`
    
    `cd ckanext-datitrentinoit`
    
    `python setup.py develop`

    `pip install -r dev-requirements.txt`


---------------------
Managing translations
---------------------

The datitrentinoit extension implements the ITranslation CKAN's interface so the translations procedure of the GUI elements is automatically covered using the translations files provided in the i18n directory. 

## Creating a new translation
To create a new translation proceed as follow:

1. Extract new messages from your extension updating the pot file::

     `python setup.py extract_messages`
     
2.  Create a translation file for your language (a po file) using the existing pot file in this plugin::

     `python setup.py init_catalog --locale YOUR_LANGUAGE`

     Replace YOUR_LANGUAGE with the two-letter ISO language code (e.g. es, de).
     
3. Do the translation into the po file

4. Once the translation files (po) have been updated, either manually or via Transifex, compile them by running::

     `python setup.py compile_catalog --locale YOUR_LANGUAGE`
     
## Updating an existing translation
In order to update the existing translations proceed as follow:

1. Extract new messages from your extension updating the pot file::

     `python setup.py extract_messages`
     
2. Update the strings in your po file, while preserving your po edits, by doing::

     `python setup.py update_catalog --locale YOUR-LANGUAGE`

3. Once the translation files (po) have been updated adding the new translations needed, compile them by running::

     `python setup.py compile_catalog --locale YOUR_LANGUAGE`