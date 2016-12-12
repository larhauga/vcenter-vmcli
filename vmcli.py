#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import json
import argparse
import requests
from tabulate import tabulate
from ConfigParser import ConfigParser
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
sslverify = False

config = ConfigParser()
config.read(['vmcli.conf', os.path.expanduser('~/.config/vmcli.conf')])
VC_URL=config.get('vmcli','url')
VC_USER=config.get('vmcli','user')
VC_PASSWORD=config.get('vmcli','password')

def vc_login():
    s = requests.Session()
    login = s.post(VC_URL + '/rest/com/vmware/cis/session', verify=sslverify,
            auth=HTTPBasicAuth(VC_USER, VC_PASSWORD))

    if login.status_code == 401:
        raise Exception('Login failed: %s' % login.json())
    elif not login.ok:
        raise Exception('Failure logging in: %s' % login.text)

    # Header: vmware-api-session-id:<token>
    s.headers.update({'Authorization': 'vmware-api-session-id:%s' % login.json()['value']})
    return s

def _vmid_from_name(s, name):
    vmlist = s.get(VC_URL + '/rest/vcenter/vm?filter.names=%s' % name)
    try:
        found = len(vmlist.json()['value'])
    except:
        found = 0
    if found < 1:
        raise Exception("No vm found")
    elif found > 1:
        raise Exception("More than one vm found")
    else:
        vmid = vmlist.json()['value'][0]['vm']
    return vmid, vmlist.json()['value'][0]

def vm_list(s):
    vms = s.get(VC_URL + '/rest/vcenter/vm')

    header = ['vm', 'name', 'power_state', 'cpu_count', 'memory_size_MiB']
    l = []
    for d in vms.json()['value']:
        l.append([d['vm'], d['name'], d['power_state'], d['cpu_count'], d['memory_size_MiB']])
    print(tabulate(l, tablefmt='psql', headers=header))

def vm_info(s, name):
    vmid, baseinfo = _vmid_from_name(s, name)
    info = s.get(VC_URL + '/rest/vcenter/vm/%s' % vmid)
    import yaml
    print(yaml.dump(yaml.load(json.dumps(info.json())), default_flow_style=False))

def vm_create(s, name):
    # Get info from network and datastore
    # /rest/vcenter/datacenter
    # /rest/vcenter/cluster
    # /rest/vcenter/datastore
    # /rest/vcenter/network

    s = vc_login()

    datacenter = s.get(VC_URL + '/rest/vcenter/datacenter', verify=sslverify)
    cluster = s.get(VC_URL + '/rest/vcenter/cluster', verify=sslverify)
    datastore = s.get(VC_URL + '/rest/vcenter/datastore', verify=sslverify)
    network = s.get(VC_URL + '/rest/vcenter/network', verify=sslverify)
    folder = s.get(VC_URL + '/rest/vcenter/folder', verify=sslverify)
    host = s.get(VC_URL + '/rest/vcenter/host', verify=sslverify)
    resourcepool = s.get(VC_URL + '/rest/vcenter/resource-pool', verify=sslverify)

    vms = s.get(VC_URL + '/rest/vcenter/vm', verify=sslverify)

    vm_create_spec = { "spec": {
        "boot": {
            "delay": 1,
            #"efi_legacy_boot": True,
            "enter_setup_mode": True,
            #"network_protocol": "IPV4",
            "retry": False,
            "retry_delay": 10,
            "type": "BIOS"
            },
        "boot_devices": [],
        #"cdrooms": [],
        "cpu": {
            "cores_per_socket": 1,
            "count": 1,
            "hot_add_enabled": True,
            "hot_remove_enabled": True
        },
        "disks": [
            {
                "new_vmdk": {
                    "capacity": 1024*1024*1024
                }
                # "backing": {
                    # "type": "VMDK_FILE" ,
                    # "vmdk_file": "[datastore1] test/test_0.vmdk"
                # },
                # "capacity": 1024*1024*1024,
                # "label": "Hard disk 1",
                # "scsi": {
                    # "bus": 0,
                    # "unit": 0
                # },
                # "type": "SCSI"
            }
        ],
        # "floppies": [],
        "guest_OS": "CENTOS_7_64",
        # "hardware": {
            # "upgrade_policy": "NEVER",
            # "upgrade_status": "NONE",
            # "version": "VMX_13"
        # },
        "memory": {
            "hot_add_enabled": True,
            # "hot_add_increment_size_MiB": 128,
            # "hot_add_limit_MiB": 8000,
            "size_MiB": 2048
        },
        "name": name,
        "nics": [
            {
                "allow_guest_control": True,
                "backing": {
                    #"distributed_port": network.json()['value'][0]['name'],
                    "type": network.json()['value'][0]['type'],
                    "network": network.json()['value'][0]['network']
                },
                "mac_type": "GENERATED",
                "start_connected": True,
                "type": "VMXNET3"
            }
        ],
        "parallel_ports": [],
        "placement": {
                "cluster": cluster.json()['value'][0]['cluster'],
                "datastore": datastore.json()['value'][0]['datastore'],
                "folder": folder.json()['value'][4]['folder'],
                "host": host.json()['value'][0]['host'],
                "resource_pool": resourcepool.json()['value'][0]['resource_pool']
        },
        # "scsi_adapters": [{
                # "bus": 0,
                # "sharing": "NONE",
                # "type": "BUSLOGIC"
            # }
        # ],
        "serial_ports": []
        }
    }


    print(json.dumps(vm_create_spec, sort_keys=True, indent=2))
    create = s.post(VC_URL + '/rest/vcenter/vm', json=vm_create_spec, headers={'Content-Type': 'application/json'}, verify=sslverify)
    print(create.text)

    created = s.get(VC_URL + '/rest/vcenter/vm/' + create.json()['value'], verify=sslverify)
    print(created.text)

def vm_delete(s, name):
    vmid, baseinfo = _vmid_from_name(s, name)
    print(vmid)
    delete = s.delete(VC_URL + '/rest/vcenter/vm/%s' % vmid)
    print(delete.text)

def vm_change_mem(s, name, size):
    vmid, baseinfo = _vmid_from_name(s, name)
    updated = s.patch(VC_URL + '/rest/vcenter/vm/%s/hardware/memory' % vmid, json={'spec': {'size_MiB': size}})
    print(updated.status_code)

def vm_power(s, name, state):
    vmid, baseinfo = _vmid_from_name(s, name)
    if state == 'get':
        print('VM %s is %s' % (name, baseinfo['power_state']))
    else:
        changestate = s.post(VC_URL + '/rest/vcenter/vm/%s/power/%s' % (vmid, state))
        print(changestate.text)

def main():
    parser = argparse.ArgumentParser(description='VMware REST API handler')
    parser.add_argument('-l', '--list', action='store_true', help='List all vms')
    parser.add_argument('-i', '--info', action='store_true', help='Get information about VM')
    parser.add_argument('-c', '--create', action='store_true', help='Create VM')
    parser.add_argument('-d', '--delete', action='store_true', help='Delete VM')
    parser.add_argument('-m', '--change-mem', type=int, help='RAM size of VM in MB')
    parser.add_argument('-p', '--power', type=str, choices=['get', 'reset', 'start', 'stop', 'suspend'], help="Power management")
    parser.add_argument('server', help="Full servername visible in VMware")
    args = parser.parse_args()

    s = vc_login()

    if args.list:
        vm_list(s)
    elif args.info:
        vm_info(s, args.server)
    elif args.create:
        vm_create(s, args.server)
    elif args.delete:
        vm_delete(s, args.server)
    elif args.change_mem:
        vm_change_mem(s, args.server, args.change_mem)
    elif args.power:
        vm_power(s, args.server, args.power)
    else:
        parser.print_help()
    # print(json.dumps(inventory(result), sort_keys=True, indent=2))

if __name__ == '__main__':
    main()
