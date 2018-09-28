
## PREPARING THE SYSTEM FOR DCAT_AP-IT

### OUTDATED DOCUMENTATION (this was used to install the first version on ckanext-dcatapit [1.0.0])

This ckanext-datitrentinoit has been updated to integrate the old version of this extension with ckanext-dcatapit 1.0.0:

	Follow the steps below only the first time you prepare the system for installing the ckanext-dcatapit.

1. Backup the DB ckan:
	
		su postgres

		pg_dump -U postgres -i ckan > ckan.dump
		
2. Install the ckanext-dcat extension:

		. /usr/local/app_loc/geosolutions/bin/activate

		cd /usr/local/data_loc/src

		git clone https://github.com/ckan/ckanext-dcat.git

		cd ckanext-dcat

		pip install -e .

		pip install -r requirements.txt
		
	- Edit the `/usr/local/app_loc/geosolutions/conf/production.ini` adding plugins:
	
		ckan.plugins = dcat dcat_rdf_harvester dcat_json_harvester dcat_json_interface

3. Update the ckanext-multilang extension:

		. /usr/local/app_loc/geosolutions/bin/activate

		cd /usr/local/data_loc/src/ckanext-multilang
		
		git checkout master

		git pull

		pip install -e .

4. Update the ckanext-datitrentinoit extension:

		. /usr/local/app_loc/geosolutions/bin/activate

		cd /usr/local/data_loc/src/ckanext-datitrentinoit

		git pull 

		git checkout dcatapit

		pip install -e .
		
	- Update the `/usr/local/app_loc/geosolutions/conf/production.ini` file removing the property below:
	
			ckan.i18n_directory

5. Uninstall the old ckanext-harvest-tn extenstion (now available in the new ckanext-datitrentinoit):

		. /usr/local/app_loc/geosolutions/bin/activate
		
		cd /usr/local/data_loc/src/ckanext-harvest-tn
		
		pip uninstall .
		
		rm -rf /usr/local/data_loc/src/ckanext-harvest-tn
		
6. Install the ckanext-dcatapit following the steps reported [here](https://github.com/geosolutions-it/ckanext-dcatapit#installation):

	**Ingore the point number 1**
	
		Pay attention that in the datitrentinoit system the paths below change from ones reported in the ckanext-dcatapit installation README:
		
			. /usr/lib/ckan/default/bin/activate -> . /usr/local/app_loc/geosolutions/bin/activate
			
			/etc/ckan/default/production.ini     -> /usr/local/app_loc/geosolutions/conf/production.ini
			
			/usr/lib/ckan/default/src            -> /usr/local/data_loc/src
		
7. Run the SQL migration script to update DB tables (make sure to have rights to execute the sql file as user postgres):

		su postgres

		psql -U postgres -d ckan -f /usr/local/data_loc/src/ckanext-datitrentinoit/migration/sql/migration.sql
	
8. Restart CKAN

9. Rebuild the Solr indexes:

		. /usr/local/app_loc/geosolutions/bin/activate

		paster --plugin=ckan search-index rebuild  -c /usr/local/app_loc/geosolutions/conf/production.ini
