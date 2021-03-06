#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: delete_source a sumocli cmdlet that removes a source

Usage:
   $ python  delete_source [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumocli_delete_source
    @version        1.00
    @author-name    Wayne Schmidt
    @author-email   wschmidt@sumologic.com
    @license-name   GNU GPL
    @license-url    http://www.gnu.org/licenses/gpl.html
"""

__version__ = 1.00
__author__ = "Wayne Schmidt (wschmidt@sumologic.com)"

### beginning ###
import json
import pprint
import os
import sys
import argparse
import http
import requests
sys.dont_write_bytecode = 1

MY_CFG = 'undefined'
PARSER = argparse.ArgumentParser(description="""
delete_source is a Sumo Logic cli cmdlet deleting a specific source
""")


PARSER.add_argument("-a", metavar='<secret>', dest='MY_SECRET', \
                    help="set api (format: <key>:<secret>) ")
PARSER.add_argument("-k", metavar='<client>', dest='MY_CLIENT', \
                    help="set key (format: <site>_<orgid>) ")
PARSER.add_argument("-e", metavar='<endpoint>', dest='MY_ENDPOINT', \
                    help="set endpoint (format: <endpoint>) ")
PARSER.add_argument("-m", default=0, metavar='<myselfid>', \
                    dest='myselfid', help="provide specific id to lookup")
PARSER.add_argument("-p", default=0, metavar='<parentid>', \
                    dest='parentid', help="provide parent id to locate with")
PARSER.add_argument("-v", type=int, default=0, metavar='<verbose>', \
                    dest='verbose', help="Increase verbosity")

ARGS = PARSER.parse_args()

if ARGS.MY_SECRET:
    (MY_APINAME, MY_APISECRET) = ARGS.MY_SECRET.split(':')
    os.environ['SUMO_UID'] = MY_APINAME
    os.environ['SUMO_KEY'] = MY_APISECRET

if ARGS.MY_CLIENT:
    (MY_DEPLOYMENT, MY_ORGID) = ARGS.MY_CLIENT.split('_')
    os.environ['SUMO_LOC'] = MY_DEPLOYMENT
    os.environ['SUMO_ORG'] = MY_ORGID
    os.environ['SUMO_TAG'] = ARGS.MY_CLIENT

if ARGS.MY_ENDPOINT:
    os.environ['SUMO_END'] = ARGS.MY_ENDPOINT
else:
    os.environ['SUMO_END'] = os.environ['SUMO_LOC']

if ARGS.myselfid:
    os.environ['MYSELFID'] = ARGS.myselfid

if ARGS.parentid:
    os.environ['PARENTID'] = ARGS.parentid

try:
    SUMO_UID = os.environ['SUMO_UID']
    SUMO_KEY = os.environ['SUMO_KEY']
    SUMO_LOC = os.environ['SUMO_LOC']
    SUMO_ORG = os.environ['SUMO_ORG']
    SUMO_END = os.environ['SUMO_END']
    MYSELFID = os.environ['MYSELFID']
    PARENTID = os.environ['PARENTID']

except KeyError as myerror:
    print('Environment Variable Not Set :: {} '.format(myerror.args[0]))

BACKUP_DIR = '/var/tmp'
BACKUP_FILE = SUMO_END + '_' + SUMO_ORG + '.' + MYSELFID + '.' + 'json'
BACKUP_TARGET = os.path.join(BACKUP_DIR, BACKUP_FILE)

PP = pprint.PrettyPrinter(indent=4)

### beginning ###
def main():
    """
    Setup the Sumo API connection, using the required tuple of region, id, and key.
    Once done, then issue the command required
    """
    source = SumoApiClient(SUMO_UID, SUMO_KEY, SUMO_END)
    run_sumo_cmdlet(source)

def run_sumo_cmdlet(source):
    """
    This will collect the information on object for sumologic and then collect that into a list.
    the output of the action will provide a tuple of the orgid, objecttype, and id
    """
    target_object = "source"
    target_dict = dict()
    target_dict["orgid"] = SUMO_ORG
    target_dict[target_object] = dict()

    src_items = source.get_sources(PARENTID)
    for src_item in src_items:
        if str(src_item['id']) == str(MYSELFID):
            target_dict[target_object][src_item['id']] = dict()
            target_dict[target_object][src_item['id']].update({'parent' : SUMO_ORG})
            target_dict[target_object][src_item['id']].update({'id' : src_item['id']})
            target_dict[target_object][src_item['id']].update({'name' : src_item['name']})
            target_dict[target_object][src_item['id']].update({'dump' : src_item})

    with open(BACKUP_TARGET, 'w') as outputobject:
        outputobject.write(json.dumps(target_dict, indent=4))

    src_items = source.delete_source(PARENTID, MYSELFID)

#### class ###
class SumoApiClient():
    """
    This is defined SumoLogic API Client
    The class includes the HTTP methods, cmdlets, and init methods
    """

    def __init__(self, access_id, access_key, region, cookieFile='cookies.txt'):
        """
        Initializes the Sumo Logic object
        """
        self.session = requests.Session()
        self.session.auth = (access_id, access_key)
        self.session.headers = {'content-type': 'application/json', \
            'accept': 'application/json'}
        self.apipoint = 'https://api.' + region + '.sumologic.com/api'
        cookiejar = http.cookiejar.FileCookieJar(cookieFile)
        self.session.cookies = cookiejar

    def delete(self, method, params=None, headers=None, data=None):
        """
        Defines a Sumo Logic Delete operation
        """
        response = self.session.delete(self.apipoint + method, \
            params=params, headers=headers, data=data)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def get(self, method, params=None, headers=None):
        """
        Defines a Sumo Logic Get operation
        """
        response = self.session.get(self.apipoint + method, \
            params=params, headers=headers)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def post(self, method, data, headers=None, params=None):
        """
        Defines a Sumo Logic Post operation
        """
        response = self.session.post(self.apipoint + method, \
            data=json.dumps(data), headers=headers, params=params)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def put(self, method, data, headers=None, params=None):
        """
        Defines a Sumo Logic Put operation
        """
        response = self.session.put(self.apipoint + method, \
            data=json.dumps(data), headers=headers, params=params)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

#### class ###
### methods ###

    def get_collectors(self):
        """
        Using an HTTP client, this uses a GET to retrieve all collectors information.
        """
        url = "/v1/collectors"
        body = self.get(url).text
        results = json.loads(body)['collectors']
        return results

    def get_collector(self, myselfid):
        """
        Using an HTTP client, this uses a GET to retrieve single collector information.
        """
        url = "/v1/collectors/" + str(myselfid)
        body = self.get(url).text
        results = json.loads(body)['collector']
        return results

    def get_sources(self, parentid):
        """
        Using an HTTP client, this uses a GET to retrieve for all sources for a given collector
        """
        url = "/v1/collectors/" + str(parentid) + '/sources'
        body = self.get(url).text
        results = json.loads(body)['sources']
        return results

    def get_source(self, parentid, myselfid):
        """
        Using an HTTP client, this uses a GET to retrieve a given source for a given collector
        """
        url = "/v1/collectors/" + str(parentid) + '/sources/' + str(myselfid)
        body = self.get(url).text
        results = json.loads(body)['sources']
        return results

    def delete_source(self, parentid, myselfid):
        """
        Using an HTTP client, this deletes a source from a collector
        """
        url = "/v1/collectors/" + str(parentid) + "/sources/" + str(myselfid)
        results = self.delete(url)
        return results

### methods ###

if __name__ == '__main__':
    main()
