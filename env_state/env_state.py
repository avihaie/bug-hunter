import json, logging
import requests
import time
from tabulate import tabulate

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - ''%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class EnvState:
    """
    Class for queering the engine for status of different resources (through API) and writing the results to txt file
    """
    def __init__(self, engine_uri, engine_pass):
        self.resource_lst = ['storagedomains', 'hosts', 'clusters', 'datacenters', 'vms', 'networks', 'templates', 'disks', 'vnicprofiles']
        self.engine_uri = engine_uri
        self.engine_pass = engine_pass

    def get_resources_stats(self):
        for resource in self.resource_lst:
            url_for_resource = 'https://%s/ovirt-engine/api/%s?accept=application/json' % (self.engine_uri, resource)
            try:
                response = requests.get(url_for_resource, auth=('admin@internal', self.engine_pass), verify=False)
                resource_dict = json.loads(response.content)
                resource_stats = self.parse_response(resource_dict=resource_dict)
            except Exception as e:
                logger.error("Something bad occurred when queering the engine with: " + url_for_resource)

    def parse_response(self, resource_dict):
        try:
            resource_stat = [(i[u'name'].encode('utf-8'),i['status'].encode('utf-8')) for i in resource_dict[resource_dict.keys()[0]]]
        except KeyError:

            try:
                resource_stat = [(i[u'name'].encode('utf-8'),i['external_status'].encode('utf-8')) for i in resource_dict[resource_dict.keys()[0]]]
            except KeyError:
                pass
            pass

    # for i in resource_stat:
    print tabulate([[ i[0], i[1] ] for i in resource_stat], headers=['Resource', 'State'])

    datefmt = '%Y-%m-%d %H:%M:%S'
    timestr = time.strftime(datefmt)

    report_file_name = 'report_%s.txt' % timestr

    with open(report_file_name, 'a') as f:
        f.write(tabulate([[ i[0], i[1] ] for i in resource_stat], headers=['Resource', 'State']))
    print('sa')
