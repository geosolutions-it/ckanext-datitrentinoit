# -*- coding: utf-8 -*-

import json
import logging
import datetime

from hashlib import sha1

from ckanext.datitrentinoit.model.statweb_metadata import StatWebMetadataPro, StatWebMetadataSubPro

log = logging.getLogger(__name__)

tags_remove = [
    'rdnt', 'siat', 'pup', 'db prior 10k', 'pup; rndt',
    'inquadramenti di base', 'suap', 'scritte', 'pupagri', 'pupasc', 'pupbos',
]

tags_subs = {
    'bosc':             'boschi',
    'comun':            'comuni',
    'siti archeolog':   'siti archeologici',
    'archeolog':        'archeologia',
    'specchio d\'acqua': 'specchi d\'acqua',
    'tratte':           'tratte ferroviarie',
    'viabilità di progetto':    'viabilità',
    'viabilità ferroviaria':    'viabilità',
    'viafer':                   'viabilità',
    'viabilità forestale':      'viabilità',
    'zps':                      'zone protezione speciale',
    'udf':                      'distretti forestali',
    'uffici distrettuali forestali': 'distretti forestali',
    'pascolo':                  'pascoli',
    'idrografici':              'idrografia',
}

# gruppi:
#["agricoltura", "ambiente", "amministrazione", "cat-meteo",
# "clima", "conoscenza", "cultura", "demografia", "economia",
# "gestione-del-territorio", "mobilita", "politica", "salute",
# "sanita", "sicurezza", "sport", "test-categoria", "turismo", "welfare"]

DEFAULT_GROUP_PRO = 'conoscenza'

# mappa Settore verso Categorie
cat_map_pro = {
    u'agricoltura':     'economia',
    u'pesca':           'economia',
    u'silvicoltura':    'economia',
    u'commercio con l\'estero':     'economia',
    u'commercio con l\'estero e internazionalizzazione': 'economia',
    u'internazionalizzazione':      'economia',
    u'conti economici':             'economia',
    u'pubblica amministrazione': 'amministrazione',
    u'istruzione formazione':    'conoscenza',
    u'istruzione e formazione':  'conoscenza',
    u'ricerca':                  'conoscenza',
    u'sviluppo e innovazione':   'conoscenza',
    u'mercato del lavoro':               'welfare',
    u'salute':                           'welfare',
    u'famiglie e comportamenti sociali': 'welfare',
    u'assistenza e protezione sociale':  'welfare',
    u'popolazione':                      'demografia',
    u'società dell\'informazione':       'demografia',
}

DEFAULT_GROUP_SUBPRO = 'conoscenza'

cat_map_sub = {
    "l'ambiente e il territorio":   "gestione-del-territorio",
    'le infrastrutture':            "gestione-del-territorio",
    'popolazione':                  "demografia",
    'famiglie e comportamenti sociali': 'demografia',
    'istruzione e formazione':      'conoscenza',
    'mercato del lavoro':           'economia',
    'le imprese, la formazione e la valorizzazione del capitale produttivo':
                                    'economia',
    'agricoltura':                  'economia',
    'servizi':                      'economia',
    'agricoltura, silvicoltura, pesca': 'economia',
}

tipoindicatore_map = {
    'R': 'Rapporto',
    'M': 'Media',
    'I': 'Incremento anno precedente',
}

def create_base_dict(guid, metadata, config):
    """
    metadata : StatWebMetadata
       The base statweb metadata object
       
    config : dict
       The configuration set at harvester level
    """

    def dateformat(d):
        return d.strftime(r"%Y-%m-%d")
        return d.isoformat()

    start_date = metadata.get_anno_inizio() or '1970'
    if len(start_date) < 4:
        log.warn("Bad annoinizio found: '%s'", start_date)
        start_date = '1970'
    created = datetime.datetime(int(start_date), 1, 1)

    last_update = metadata.get_ultimo_aggiornamento() or "01/01/1970"
    day, month, year = [int(a) for a in last_update.split('/')]
    updated = datetime.datetime(year, month, day)

    now = dateformat(datetime.datetime.now())

    package_dict = {
        'title':             metadata.get_descrizione(),
        'groups':            config.get('groups', [{'name': 'statistica'}]),
        'author':           'Servizio Statistica',
        'author_email':     'serv.statistica@provincia.tn.it',
        'maintainer':       'Servizio Statistica',
        'maintainer_email': 'serv.statistica@provincia.tn.it',
        'metadata_modified': now,
         #'tags':              tags,  # i tag non sembrano essere valorizzati
        'license_id':       'cc-by',
        'license':          'Creative Commons Attribution',
        'license_title':    'Creative Commons Attribution 2.5 it',
        'license_url':      'http://creativecommons.org/licenses/by/2.5/it/',
        'isopen':            True,
        'resources':         []
    }

    extras = {
        'holder_name': 'Provincia Autonoma di Trento',
        'geographical_name': 'ITA_TRT',
        'geographical_geonames_url': 'http://www.geonames.org/3165243',
        'temporal_start': dateformat(created),
        'frequency': metadata.get_frequenza(),
        'issued': now,
        'modified': dateformat(updated),
        'encoding': 'UTF-8',
        'Algoritmo':         metadata.get_algoritmo(),
        'Anno di inizio':    metadata.get_anno_inizio(),
        'Measurement unit':  metadata.get_um(),
    }

    return package_dict, extras


def create_pro_package_dict(guid, orig_id, metadata, config):
    """
    :param StatWebMetadataPro metadata:  The statweb metadata object for PRO level.
    ;param dict config:  The configuration set at harvester level.
    :return: the package dict.
    :rtype: dict
    """

    package_dict, extras = create_base_dict(guid, metadata, config)

    extras['Fenomeno'] =  metadata.get_fenomeno()
    extras['Confronti territoriali'] = metadata.get_confronti()
    extras['_harvest_source'] = 'statistica:' + orig_id

    package_dict['extras'] = _extras_as_dict(extras)

    groupname = cat_map_pro.get((metadata.get_settore() or 'default').lower(), DEFAULT_GROUP_PRO)
    groups = [{'name': groupname}]

    description = create_pro_description(metadata)

    package_dict['id'] = sha1('statistica:' + orig_id).hexdigest(),
    package_dict['url'] = 'http://www.statweb.provincia.tn.it/INDICATORISTRUTTURALI/ElencoIndicatori.aspx'
    package_dict['groups'] = groups
    package_dict['notes'] = description

    return package_dict

def create_subpro_package_dict(guid, metadata, config):
    """
    metadata : StatWebMetadataSubPro
               The statweb metadata object for SUB PRO level

    config : dict
       The configuration set at harvester level
    """

    orig_id = metadata.get_id()

    package_dict, extras = create_base_dict(guid, metadata, config)

    extras['Fonte'] =  metadata.get_fonte()
    extras['Tipo di Fenomeno'] =  metadata.get_tipo_fenomeno()
    extras['Tipo di Indicatore'] =  metadata.get_tipo_indicatore()
    extras['Settore'] =  metadata.get_settore()
    extras['Livello Geografico Minimo'] =  metadata.get_min_livello()
    extras['_harvest_source'] = 'statistica_subpro:' + orig_id

    package_dict['extras'] = _extras_as_dict(extras)

    groupname = cat_map_sub.get((metadata.get_settore() or 'default').lower(), DEFAULT_GROUP_SUBPRO)
    groups = [{'name': groupname}]

    description = create_subpro_description(metadata)

    package_dict['id'] = sha1('statistica_subpro:' + orig_id).hexdigest(),
    package_dict['url'] = 'http://www.statweb.provincia.tn.it/INDICATORISTRUTTURALISubPro/'
    package_dict['groups'] = groups
    package_dict['notes'] = description

    return package_dict

def create_pro_description(metadata):
    d = ''
    d = _add_field(d, 'Area', metadata.get_area())
    d = _add_field(d, 'Settore', metadata.get_settore())
    d = _add_field(d, 'Algoritmo', metadata.get_algoritmo())
    d = _add_field(d, 'Fenomeno', metadata.get_fenomeno())
    d = _add_field(d, 'Confronti territoriali', metadata.get_confronti())

    return d

def create_subpro_description(metadata):
    d = ''
    d = _add_field(d, 'Settore', metadata.get_settore())
    d = _add_field(d, 'Algoritmo', metadata.get_algoritmo())
    d = _add_field(d, 'Tipo Indicatore', tipoindicatore_map.get(metadata.get_tipo_indicatore()))
    d = _add_field(d, 'Livello Geografico Minimo', metadata.get_min_livello())

    return d

def _add_field(base, label, data):
    if data:
        return base + '**' + label + ':** ' + data + '\n\n'
    else:
        return base

def _extras_as_dict(extras):
    extras_as_dict = []
    for key, value in extras.iteritems():
        if isinstance(value, (list, dict)):
            extras_as_dict.append({'key': key, 'value': json.dumps(value)})
        else:
            extras_as_dict.append({'key': key, 'value': value})

    return extras_as_dict
