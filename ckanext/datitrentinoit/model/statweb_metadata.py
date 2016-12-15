# -*- coding: utf-8 -*-

import json
import logging

log = logging.getLogger(__name__)


class StatWebProIndex(object):
    '''
    Documento base di statweb, che contiene una lista delle info base
    (id e URL) dei dataset.
    '''

    entries = {}  # guid: StatWebProEntry

    def __init__(self, str):
        assert (str is not None), 'Index missing'
        self.__parse(str)

    def __parse(self, str):
        '''Add all the Entries found in the response'''
        
        index = _safe_decode(str)

        name, entrylist = index.popitem()

        log.info("Found %s entries in %s index", len(entrylist), name)

        for jsonentry in entrylist:
            if jsonentry is None:
                log.info("Empty entry in IndicatoriStrutturali")
                continue

            entry = StatWebProEntry(obj=jsonentry)
            self.entries[entry.build_guid()] = entry

    def keys(self):
        return set(self.entries.keys())

    def get_as_string(self, guid):
        return self.entries[guid].tostring()


class StatWebProEntry(object):
    '''
    Info base del dataset Pro.
    Viene salvato come content dell'harvest_object serializzato come JSON.

    Inizializzato con info base (url, id) ottenuti dall'indice statweb.
    Nella key 'metadata' viene poi aggiunto il dict dei metadati ottenuti dalla chiamata
    sul singolo dataset.
    '''

    obj = None

    def __init__(self, str=None, obj=None):
        assert (str is not None or obj is not None), 'StatWebProEntry: Missing input'
        assert (str is None or obj is None), 'StatWebProEntry: Must provide a single input'
        if (obj is not None):
            self.obj = obj
        else:
            self.obj = _safe_decode(str)

    def build_guid(self):
        return 'statistica:' + self.get_id()

    def get_id(self):
        return str(self.obj['id'])

    def get_url(self):
        return str(self.obj['URL'])

    def set_metadata(self, metadataobj):
        self.obj['metadata'] = metadataobj

    def get_metadata(self):
        return self.obj['metadata']

    def tostring(self):
        encoder = json.JSONEncoder()
        return encoder.encode(self.obj)


class StatWebMetadata(object):  # abstract
    '''
    Contiene info comuni ai metadati di statspro e statssubpro
    '''

    metadata = None
    stat_type = None

    def __init__(self, stype, str=None, obj=None):
        assert (str is not None or obj is not None), 'StatWebMetadata: Missing input'
        if (obj is not None):
            self.metadata = obj
        else:
            try:
                decoded = _safe_decode(str)
                metadata_list = decoded.values()[0]
                self.metadata = metadata_list[0]
            except ValueError as e:
                log.warn("Error parsing string\n%s", str)
                import traceback
                traceback.print_exc()
                raise e

        self.stat_type = stype

    def get_stat_type(self):
        return self.stat_type

    def get_obj(self):
        return self.metadata

    def get(self, key):
        return self.metadata.get(key)

    def get_descrizione(self):
        return self.metadata.get('Descrizione')

    def get_settore(self):
        return self.metadata.get('Settore')

    def get_algoritmo(self):
        return self.metadata.get('Algoritmo')

    def get_ultimo_aggiornamento(self):
        return self.metadata.get('UltimoAggiornamento')

    def get_anno_inizio(self):
        return self.metadata.get('AnnoInizio')

        # un paio di field encodati in key diverse in pro e subpro
    def get_frequenza(self):
        return self.metadata.get('FreqAggiornamento') or self.metadata.get('FrequenzaAggiornamento')

    def get_um(self):
        return self.metadata.get(u'UnitàMisura') or self.metadata.get('UM')


class StatWebMetadataPro(StatWebMetadata):

    def __init__(self, str=None, obj=None):
        StatWebMetadata.__init__(self, 'stat', str=str, obj=obj)

    def get_area(self):
        return self.metadata.get('Area')

    def get_fenomeno(self):
        return self.metadata.get('Fenomeno')

    def get_confronti(self):
        return self.metadata.get('ConfrontiTerritoriali')


class StatWebMetadataSubPro(StatWebMetadata):

    def __init__(self, str=None, obj=None):
        assert (str is not None or obj is not None), 'StatWebMetadata: Missing input'
        if (obj is not None):
            StatWebMetadata.__init__(self, 'SP', obj=obj)
        else:
            try:
                decoded = _safe_decode(str)
                StatWebMetadata.__init__(self, 'SP', obj=decoded)

            except ValueError as e:
                log.warn("Error parsing string\n%s", str)
                import traceback
                traceback.print_exc()
                raise e        

    def build_guid(self):
        return 'subpro:' + self.get_id()

    def get_id(self):
        return self.metadata.get('id')

    def get_min_livello(self):
        return self.metadata.get('LivelloGeograficoMinimo')

    def get_tipo_indicatore(self):
        return self.metadata.get('TipoIndicatore')

    def get_anno_base(self):
        return self.metadata.get('AnnoBase')

    def get_fonte(self):
        return self.metadata.get('Fonte')

    def get_tipo_fenomeno(self):
        return self.metadata.get('TipoFenomento')

    def tostring(self):
        encoder = json.JSONEncoder()
        return encoder.encode(self.metadata)



class StatWebSubProIndex(object):
    '''
    Documento base di statweb subpro, che contiene indice e contenuti subpro
    '''

    entries = {}  # id: StatWebMetadataSubPro

    def __init__(self, str):
        assert (str is not None), 'Index missing'
        self.__parse(str)

    def __parse(self, str):
        '''Add all the Entries found in the response'''

        index = _safe_decode(str)

        name, entrylist = index.popitem()

        log.info("Found %s entries in %s index", len(entrylist), name)

        for jsonentry in entrylist:
            if jsonentry is None:
                log.info("Empty entry in SubPro index")
                continue

            entry = StatWebMetadataSubPro(obj=jsonentry)
            self.entries[entry.build_guid()] = entry

    def keys(self):
        return set(self.entries.keys())

    def get_as_string(self, guid):
        return self.entries[guid].tostring()


class SubProMetadata(object):
    '''
    Contiene info sui subdataset subpro
    '''

    metadata = None

    def __init__(self, str=None):
        assert (str is not None), 'SubProMetadata: Missing input'

        maindict = _safe_decode(str)
        name, entrylist = maindict.popitem()

        log.info('Found %s entries in index "%s"', len(entrylist), name)
        self.metadata = entrylist[0]

    def get_descrizione(self):
        return self.metadata.get('descrizione')

    def get_data_url(self):
        return self.metadata.get('URLTabD')

    def get_ultimo_aggiornamento(self):
        return self.metadata.get('UltimoAggiornamento')


def _safe_decode(str):
    try:
        return json.JSONDecoder().decode(str)
    except ValueError as e:
        log.warn("Error parsing string, Trying unrestricted parsing...")
        return json.JSONDecoder(strict=False).decode(str) # this may throw again, but it's ok: we have no other magic solution

