from setuptools import setup, find_packages
import sys

version = '0.1.1'

setup(
    name='ckanext-datitrentinoit',
    version=version,
    description="CKAN customizations for dati.trentino.it",
    long_description="CKAN customizations for dati.trentino.it",
    author="Tobia Di Pisa",
    author_email="tobia.dipisa@geo-solutions.it",
    url='http://dati.trentino.it',
    license='Affero GPL',
    classifiers=[],
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.datitrentinoit'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points='''
        [ckan.plugins]
        datitrentinoit = ckanext.datitrentinoit.plugin:DatiTrentinoPlugin
        statwebpro_harvester=ckanext.datitrentinoit.harvesters.statwebpro:StatWebProHarvester
        statwebsubpro_harvester=ckanext.datitrentinoit.harvesters.statwebsubpro:StatWebSubProHarvester
        csw_tn_harvester=ckanext.datitrentinoit.harvesters.csw_tn:CSWTNHarvester

        [babel.extractors]
        ckan = ckan.lib.extract:extract_ckan
    ''',

    # Translations
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ],
    }
)
