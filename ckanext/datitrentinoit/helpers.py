import logging
import urllib

import ckan.model as model
import ckan.plugins as p
import ckan.lib.search as search
import ckan.lib.helpers as h

import ckan.logic as logic
from ckan.common import request

import ckanext.multilang.helpers as multilang_helpers

from ckanext.multilang.model import PackageMultilang

log = logging.getLogger(__file__)


def recent_updates(n):
    #
    # Return a list of the n most recently updated datasets.
    #
    log.debug('::::: Retrrieving latest datasets: %r' % n)
    context = {'model': model,
               'session': model.Session,
               'user': p.toolkit.c.user or p.toolkit.c.author}

    data_dict = {'rows': n,
                 'sort': u'metadata_modified desc',
                 'facet': u'false'}

    try:
        search_results = logic.get_action('package_search')(context, data_dict)
    except search.SearchError, e:
        log.error('Error searching for recently updated datasets')
        log.error(e)
        search_results = {}

    for item in search_results.get('results'):
        log.info(':::::::::::: Retrieving the corresponding localized title and abstract :::::::::::::::')

        lang = multilang_helpers.getLanguage()

        q_results = model.Session.query(PackageMultilang)\
                                 .filter(PackageMultilang.package_id == item.get('id'),
                                         PackageMultilang.lang == lang).all()

        if q_results:
            for result in q_results:
                item[result.field] = result.text

    return search_results.get('results', [])

# this is a hack against ckan-2.4.0 (until 2.4.7)
# Early 2.4.x versions don't have helpers.current_url() and rely
# on unescaped CKAN_CURRENT_URL env var in request. This can cause 
# invalid redirection url in language selector.
# Details:
#  * 2.4.0: https://github.com/ckan/ckan/blob/ckan-2.4.0/ckan/lib/helpers.py#L277-L280
#  * 2.4.9: https://github.com/ckan/ckan/blob/ckan-2.4.9/ckan/lib/helpers.py#L305-L313
# fix in https://github.com/ckan/ckan/commit/109d47c1fe852085eb9bf3ba8e34d6bc6e57e3b1
#
# Relevant issues:
# https://github.com/geosolutions-it/ckanext-provbz/issues/37
# https://github.com/geosolutions-it/ckanext-provbz/issues/20#issuecomment-366279774
def hacked_current_url():
    try:
        return h.current_url()
    except AttributeError:
        return urllib.unquote(request.environ['CKAN_CURRENT_URL'])

