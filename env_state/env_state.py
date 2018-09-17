import json
import requests
import time
from tabulate import tabulate


resource_list = ['storagedomains', 'hosts', 'clusters', 'datacenters', 'vms', 'networks', 'templates', 'disks', 'vnicprofiles']
# resource_list = ['datacenters']


for resource in resource_list:
    response = requests.get('https://he-rdu-izuckerm.rhev.openstack.engineering.redhat.com/ovirt-engine/api/'
                                     + resource + '?accept=application/json',auth=('admin@internal', 'qum5net'),verify=False)
    resource_dict = json.loads(response.content)
    try:
        # tmp = [(i[u'name'].encode('utf-8'),i['external_status'].encode('utf-8')) for i in resource_dict[u'storage_domain']]
        resource_stat = [(i[u'name'].encode('utf-8'),i['status'].encode('utf-8')) for i in resource_dict[resource_dict.keys()[0]]]
    except KeyError:

        try:
            print('resource: ' + resource)
            resource_stat = [(i[u'name'].encode('utf-8'),i['external_status'].encode('utf-8')) for i in resource_dict[resource_dict.keys()[0]]]
        except KeyError:
            pass
        pass

    # for i in resource_stat:
    print tabulate([[ i[0], i[1] ] for i in resource_stat], headers=['Resource', 'State'])

    timestr = time.strftime("%Y%m%d-%H%M%S")
    report_name =
    with open('resources_stats.txt', 'a') as f:
        f.write(tabulate([[ i[0], i[1] ] for i in resource_stat], headers=['Resource', 'State']))
    print('sa')
