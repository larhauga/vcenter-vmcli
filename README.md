vmcli: Simple vCenter client for simple vm operations
=====================================================
Simple REST client library and command line tool for home and small
environments. Uses vCenter REST API and is dependent on vCenter 6.5.  
Lightweight with minimal library dependencies.

## DISCLAMER: THIS IS WORK IN PROGRESS.
This is a work in progress, and contains certain parts that are pre configured
in the code. If you choose to use this, do it as a reference and not a complete
library or client, as this code is subject to change.

I have used this as a way of understanding the workings of the vCenter REST API
and I would recomend you to do the same. However, in a standard vCenter/vSphere
environment, I recon you can use this, but then you would probably be using the
powercli extentions that there are a lot of.


## Usage

```
usage: vmcli.py [-h] [-l] [-i] [-c] [-d] [-m CHANGE_MEM]
                [-p {get,reset,start,stop,suspend}]
                server

VMware REST API handler

positional arguments:
  server                Full servername visible in VMware

optional arguments:
  -h, --help            show this help message and exit
  -l, --list            List all vms
  -i, --info            Get information about VM
  -c, --create          Create VM
  -d, --delete          Delete VM
  -m CHANGE_MEM, --change-mem CHANGE_MEM
                        RAM size of VM in MB
  -p {get,reset,start,stop,suspend}, --power {get,reset,start,stop,suspend}
                        Power management
```

