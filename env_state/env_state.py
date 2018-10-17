import argparse
import datetime
import json
import logging

import requests
import urllib3
from tabulate import tabulate

import config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - ''%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class EnvState:
    """
    Class for queering the engine for status of different resources (through API) and writing the results to txt file
    """

    def __init__(self, engine_uri, engine_pass, results_path):
        self.resource_lst = ['storagedomains', 'hosts', 'clusters', 'datacenters', 'vms', 'networks', 'templates',
                             'disks', 'vnicprofiles']
        self.engine_uri = engine_uri
        self.engine_pass = engine_pass
        self.results_path = results_path

    def parse_response(self, resource_dict):
        name_status_lst = []
        for i in range(0, len(resource_dict[resource_dict.keys()[0]])):
            if 'name' and 'status' in resource_dict[resource_dict.keys()[0]][i]:
                name_status_lst.append({resource_dict[resource_dict.keys()[0]][i]['name']:
                                        resource_dict[resource_dict.keys()[0]][i]['status']})

            elif 'name' and 'external_status' in resource_dict[resource_dict.keys()[0]][i]:
                name_status_lst.append({resource_dict[resource_dict.keys()[0]][i]['name']:
                                        resource_dict[resource_dict.keys()[0]][i]['external_status']})

            else:
                name_status_lst.append({resource_dict[resource_dict.keys()[0]][i]['name']: None})

        return name_status_lst

def get_resources_stats(engine_uri, engine_pass, results_path):
    envs_ob = EnvState(engine_uri, engine_pass, results_path)

    for resource in envs_ob.resource_lst:
        logger.info('Parsing resource: %s' % resource)
        url_for_resource = 'https://%s/ovirt-engine/api/%s?accept=application/json' % (envs_ob.engine_uri, resource)
        try:
            response = requests.get(url_for_resource, auth=('admin@internal', envs_ob.engine_pass), verify=False)
            resource_dict = json.loads(response.content)
            resource_stats = envs_ob.parse_response(resource_dict=resource_dict)

        except requests.exceptions.HTTPError as e:
            raise requests.exceptions.HTTPError(
                "Something bad occurred when queering the engine with: %s\n%s\nresponse is: %s" % (
                    url_for_resource, e, response
                )
            )

        with open(envs_ob.results_path, 'a') as f:
            f.write(tabulate([[i.items()[0][0], i.items()[0][1]] for i in resource_stats],
                             headers=[resource, 'State']))
            f.write('\n\n')


def main():
    """
    In case of manual execution -
    e.g python env_state.py -e "he-rdu-izuckerm.rhev.openstack.engineering.redhat.com" -p "<admin API password>"
     -s "/tmp/results_file.txt

    Options -
        * -e, --engine_uri : Uri for engine. without https.
        * -p, --password : Admin API password.
        * -s, --env_state_result_file_path : Full path to a file in which we want to store the environment state.
                                             By default It would be: config.LOCALHOST_LOGS_PATH/env_state_file_<date_time_now>.txt
                                             Where date time format is '%Y-%m-%d_%H:%M:%S'.
    """
    datetime_now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    parser = argparse.ArgumentParser(description='This program queries the engine for resources statuses')
    parser.add_argument('-e', '--engine_uri', action='store', dest='engine_uri', required=True,
                        help='Uri for engine. without https. Example: izuckerm.rhev.openstack.engineering.redhat.com')

    parser.add_argument('-p', '--password', action='store', dest='engine_pass', required=True,
                        help='Engine password for internal admin (API)')

    parser.add_argument('-s', '--env_state_result_file_path', action='store', dest='env_state_result_file_path',
                        help='Full path for saving results file', nargs="?",
                        const="%s/env_state_file_%s.txt" % (config.LOCALHOST_LOGS_PATH, datetime_now),
                        default="%s/env_state_file_%s.txt" % (config.LOCALHOST_LOGS_PATH, datetime_now))
    # const sets the default when there are 0 arguments. If you want to set -s to some value even if no -s is specified,
    # then include default=..  nargs=? means 0-or-1 arguments

    args = parser.parse_args()


    get_resources_stats(
        engine_uri=args.engine_uri, engine_pass=args.engine_pass, results_path=args.env_state_result_file_path
    )


if __name__ == '__main__':
    main()
