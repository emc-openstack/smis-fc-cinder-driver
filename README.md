SMI-S FC Cinder Driver for Havana
=================================

Copyright (c) 2013 EMC Corporation
All Rights Reserved

Licensed under EMC Freeware Software License Agreement
You may not use this file except in compliance with the License.
You may obtain a copy of the License at

        https://github.com/emc-openstack/freeware-eula/blob/master/Freeware_EULA_20131217_modified.md
        

Overview
--------

The EMCSMISFCDriver is based on the existing FibreChannelDriver, with the ability to create/delete and attach/detach volumes and create/delete snapshots, etc.

The EMCSMISFCDriver executes the volume operations by communicating with the backend EMC storage. It uses a CIM client in python called PyWBEM to make CIM operations over HTTP.

The EMC CIM Object Manager (ECOM) is packaged with the EMC SMI-S Provider. It is a CIM server that allows CIM clients to make CIM operations over HTTP, using SMI-S in the backend for EMC storage operations.

The EMC SMI-S Provider supports the SNIA Storage Management Initiative (SMI), an ANSI standard for storage management. It supports VMAX and VNX storage systems.

Supported OpenStack Releases
----------------------------

* This driver supports Havana.
* A driver that supports Grizzly can be obtained by contacting EMC.

Requirements
------------

EMC SMI-S Provider V4.5.1 and higher is required. SMI-S can be downloaded from EMC's support web site. SMI-S can be installed on a non-OpenStack host. Supported platforms include different flavors of Windows, RedHat, and SuSE Linux. Refer to the EMC SMI-S Provider release notes for supported platforms and installation instructions. Note that storage arrays have to be discovered on the SMI-S server before using Cinder Driver. Follow instructions in the release notes to discover the arrays.

SMI-S is usually installed at /opt/emc/ECIM/ECOM/bin on Linux and C:\Program Files\EMC\ECIM\ECOM\bin on Windows. After installing and configuring SMI-S, go to that directory and type “TestSmiProvider.exe”. After entering the test program, type “dv” and examine the output. Make sure that the arrays are recognized by the SMI-S server before using Cinder Driver.

EMC storage VMAX Family and VNX Series are supported.

Copy emc_smis_fc.py and updated emc_smis_common.py from the source location to the cinder/volume/drivers/emc folder on the server where you are running cinder-volume service.  It is usually at /usr/share/pyshared/cinder/volume/drivers/emc or /opt/stack/cinder/cinder/volume/drivers/emc.

Supported Operations
--------------------

The following operations will be supported on both VMAX and VNX arrays:
*	Create volume
*	Delete volume
*	Attach volume
*	Detach volume
*	Create snapshot
*	Delete snapshot
*	Create cloned volume
*	Copy image to volume
*	Copy volume to image

The following operations will be supported on VNX only:
*	Create volume from snapshot
*	Extend volume
 
Preparation
-----------

* Install systool and sg3-utils:
```
$sudo apt-get install sysfsutils sg3-utils
```
* Install python-pywbem package. For example:
```
$ sudo apt-get install python-pywbem
```
* Setup SMI-S. Download SMI-S from EMC's support website and install it following the instructions of SMI-S release notes. Add your VNX/VMAX arrays to SMI-S following the SMI-S release notes.
* Register with VNX.
* Create Masking View on VMAX.

Register with VNX
-----------------

For a VNX volume to be exported to a Compute node, SAN zoning needs to be configured on the node and WWNs of the node need to be registered with VNX in Unisphere.

Create Masking View on VMAX
---------------------------

For VMAX, user needs to do initial setup on the Unisphere for VMAX server first. On the Unisphere for VMAX server, create initiator group, storage group, port group, and put them in a masking view. Initiator group contains the WWNs of the openstack hosts. Storage group should have at least 6 gatekeepers.

Config file cinder.conf
-----------------------

Make the following changes in /etc/cinder/cinder.conf.

For VMAX, we have the following entries.
```
volume_driver = cinder.volume.drivers.emc.emc_smis_fc.EMCSMISFCDriver
cinder_emc_config_file = /etc/cinder/cinder_emc_config.xml
```

For VNX, we have the following entries.
```
volume_driver = cinder.volume.drivers.emc.emc_smis_fc.EMCSMISFCDriver
cinder_emc_config_file = /etc/cinder/cinder_emc_config.xml
```

Restart the cinder-volume service.

Config file cinder_emc_config.xml
---------------------------------

Create the file /etc/cinder/cinder_emc_config.xml. We don't need to restart service for this change.

For VMAX, we have the following in the xml file:
```
<?xml version='1.0' encoding='UTF-8'?>
<EMC>
<StorageType>xxxx</StorageType>
<MaskingView>xxxx</MaskingView>
<EcomServerIp>x.x.x.x</EcomServerIp>
<EcomServerPort>xxxx</EcomServerPort>
<EcomUserName>xxxxxxxx</EcomUserName>
<EcomPassword>xxxxxxxx</EcomPassword>
</EMC>
```

For VNX, we have the following in the xml file:
```
<?xml version='1.0' encoding='UTF-8'?>
<EMC>
<StorageType>xxxx</StorageType>
<EcomServerIp>x.x.x.x</EcomServerIp>
<EcomServerPort>xxxx</EcomServerPort>
<EcomUserName>xxxxxxxx</EcomUserName>
<EcomPassword>xxxxxxxx</EcomPassword>
</EMC>
```

MaskingView is required for attaching VMAX volumes to an OpenStack VM. A Masking View can be created using Unisphere for VMAX. The Masking View needs to have an Initiator Group that contains the WWNs of the OpenStack compute node that hosts the VM.

StorageType is the thin pool where user wants to create volume from.  Thin pools can be created using Unisphere for VMAX and VNX.  Note that the StorageType tag is not required in this Havana release. Refer to the following "Multiple Pools and Thick/Thin Provisioning" section on how to support thick/thin provisioning.

EcomServerIp and EcomServerPort are the IP address and port number of the ECOM server which is packaged with SMI-S. EcomUserName and EcomPassword are credentials for the ECOM server.

Multiple Pools and Thick/Thin Provisioning
------------------------------------------

This section describes how to support multiple pools and thick provisioning in addition to thin provisioning.  

The <StorageType> tag in cinder_emc_config.xml is not mandatory.  There are two ways of specifying a pool:

1. Use the <StorageType> tag.  In this case, pool name is specified in the <Storagetype> tag.  Only thin provisioning is supported.
2. Use Cinder Volume Type to define a pool name and provisioning type.  The pool name is the name of a pre-created pool.  The provisioning type could be either thin or thick. 

Here is an example of how to use method 2.   First create volume types.  Then define extra specs for each volume type.

```
cinder --os-username admin --os-tenant-name admin type-create "High Performance"
cinder --os-username admin --os-tenant-name admin type-create "Standard Performance"
cinder --os-username admin --os-tenant-name admin type-key "High Performance" set storagetype:pool=smi_pool
cinder --os-username admin --os-tenant-name admin type-key "High Performance" set storagetype:provisioning=thick
cinder --os-username admin --os-tenant-name admin type-key "Standard Performance" set storagetype:pool=smi_pool
cinder --os-username admin --os-tenant-name admin type-key "Standard Performance" set storagetype:provisioning=thin
```

In the above example, two volume types are created.  They are “High Performance” and “Standard Performance”.   For High Performance, “storagetype:pool” is set to “smi_pool” and “storagetype:provisioning” is set to “thick”.  Similarly for Standard Performance, “storagetype:pool” is set to “smi_pool” and “storagetype:provisioning” is set to “thin”.  If “storagetype:provisioning” is not specified, it will be default to thin.

Note: Volume Type names “High Performance” and “Standard Performance” are user-defined and can be any names.  Extra spec keys “storagetype:pool” and “storagetype:provisioning” have to be the exact names listed here.  Extra spec value “smi_pool” is just your pool name.  Extra spec value for “storagetype:provisioning” has to be either “thick” or “thin”.
The driver will look for volume type first.  If volume type is specified when creating a volume, the driver will look for volume type definition and find the matching pool and provisioning type.  If volume type is not specified, it will fall back to use the <StorageType> in cinder_emc_config.xml.

Multiple Backends
-----------------

Here is an example of how to support multiple backends.  To support two backends emc-vnx and emc-vmax, add the following in cinder.conf:

```
enabled_backends=emc-vnx,emc-vmax
[emc-vnx]
volume_driver = cinder.volume.drivers.emc.emc_smis_fc.EMCSMISFCDriver
cinder_emc_config_file = /etc/cinder/cinder_emc_config.xml
volume_backend_name=emc-vnx
[emc-vmax]
volume_driver = cinder.volume.drivers.emc.emc_smis_fc.EMCSMISFCDriver
cinder_emc_config_file = /etc/cinder/cinder_emc_config.vmax.xml
volume_backend_name=emc-vmax
```

Then create two volume-type referring to emc-vnx and emc-vmax:

```
root@core:/etc/init.d# cinder extra-specs-list
+--------------------------------------+----------+---------------------------------------+
|                  ID                  |   Name   |              extra_specs              |
+--------------------------------------+----------+---------------------------------------+
| 42c62c3f-fd41-4eb4-afc5-584f607c52f8 | emc-vmax | {u'volume_backend_name': u'emc-vmax'} |
| 4f8d8f90-f252-4980-ac3d-4c5a79bb9ef7 | emc-vnx  |  {u'volume_backend_name': u'emc-vnx'} |
```

In addition to “volume_backend_name” for multiple backend support, you also need to add “storagetype:pool” to the volume-type.  “storagetype:provisioning” is optional.  By default it is thin.

The following command sets pool name to “smi_pool” for volume type “Standard Performance”.
```
cinder --os-username admin --os-tenant-name admin type-key "Standard Performance" set storagetype:pool=smi_pool
```


