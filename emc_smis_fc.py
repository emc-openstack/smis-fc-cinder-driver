#!/usr/bin/python

#    Copyright (c) 2013 EMC Corporation
#    All Rights Reserved
#
#    Licensed under EMC Freeware Software License Agreement
#    You may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        https://github.com/emc-openstack/freeware-eula/
#        blob/master/Freeware_EULA_20131217_modified.md
#
"""
FC Drivers for EMC VNX and VMAX arrays based on SMI-S.

"""

import os
import time

from cinder import context
from cinder import exception
from cinder.openstack.common import log as logging
from cinder.volume import driver
from cinder.volume.drivers.emc import emc_smis_common

LOG = logging.getLogger(__name__)

class EMCSMISFCDriver(driver.FibreChannelDriver):
    """EMC FC Drivers for VMAX and VNX using SMI-S.

    Version history:
        1.0.0 - Initial driver
        1.1.0 - Multiple pools and thick/thin provisioning,
                performance enhancement.
    """

    VERSION = "1.1.0"

    def __init__(self, *args, **kwargs):

        super(EMCSMISFCDriver, self).__init__(*args, **kwargs)
        self.common = emc_smis_common.EMCSMISCommon(
                                        'FC',
                                        configuration=self.configuration)

    def check_for_setup_error(self):
        pass

    def create_volume(self, volume):
        """Creates a EMC(VMAX/VNX) volume."""
        volpath = self.common.create_volume(volume)

        ctxt = context.get_admin_context()
        model_update = {}
        volume['provider_location'] = str(volpath) 
        model_update['provider_location'] = volume['provider_location']
        self.db.volume_update(ctxt, volume['id'], model_update)

    def create_volume_from_snapshot(self, volume, snapshot):
        """Creates a volume from a snapshot."""
        volpath = self.common.create_volume_from_snapshot(volume, snapshot)

        ctxt = context.get_admin_context()
        model_update = {}
        volume['provider_location'] = str(volpath)
        model_update['provider_location'] = volume['provider_location']
        self.db.volume_update(ctxt, volume['id'], model_update)

    def create_cloned_volume(self, volume, src_vref):
        """Creates a cloned volume."""
        volpath = self.common.create_cloned_volume(volume, src_vref)

        ctxt = context.get_admin_context()
        model_update = {}
        volume['provider_location'] = str(volpath)
        model_update['provider_location'] = volume['provider_location']
        self.db.volume_update(ctxt, volume['id'], model_update)

    def delete_volume(self, volume):
        """Deletes an EMC volume."""
        self.common.delete_volume(volume)

    def create_snapshot(self, snapshot):
        """Creates a snapshot."""
        ctxt = context.get_admin_context()
        volumename = snapshot['volume_name']
        index = volumename.index('-')
        volumeid = volumename[index+1:]
        volume = self.db.volume_get(ctxt, volumeid)

        volpath = self.common.create_snapshot(snapshot, volume)

        model_update = {}
        snapshot['provider_location'] = str(volpath)
        model_update['provider_location'] = snapshot['provider_location']
        self.db.snapshot_update(ctxt, snapshot['id'], model_update)

    def delete_snapshot(self, snapshot):
        """Deletes a snapshot."""
        ctxt = context.get_admin_context()
        volumename = snapshot['volume_name']
        index = volumename.index('-')
        volumeid = volumename[index+1:]
        volume = self.db.volume_get(ctxt, volumeid)

        self.common.delete_snapshot(snapshot, volume)

    def ensure_export(self, context, volume):
        """Driver entry point to get the export info for an existing volume."""
        pass 

    def create_export(self, context, volume):
        """Driver entry point to get the export info for a new volume."""
        pass

    def remove_export(self, context, volume):
        """Driver entry point to remove an export for a volume."""
        pass

    def check_for_export(self, context, volume_id):
        """Make sure volume is exported."""
        pass

    def initialize_connection(self, volume, connector):
        """Initializes the connection and returns connection info.

        Assign any created volume to a compute node/host so that it can be
        used from that host.

        The  driver returns a driver_volume_type of 'fibre_channel'.
        The target_wwn can be a single entry or a list of wwns that
        correspond to the list of remote wwn(s) that will export the volume.
        Example return values:

            {
                'driver_volume_type': 'fibre_channel'
                'data': {
                    'target_discovered': True,
                    'target_lun': 1,
                    'target_wwn': '1234567890123',
                }
            }

            or

             {
                'driver_volume_type': 'fibre_channel'
                'data': {
                    'target_discovered': True,
                    'target_lun': 1,
                    'target_wwn': ['1234567890123', '0987654321321'],
                }
            }

        """
        device_info = self.common.initialize_connection(volume,
                connector)
        device_number = device_info['hostlunid']
        storage_system = device_info['storagesystem']
        ports = self.common.get_target_wwns(storage_system, connector)

        data = {'driver_volume_type': 'fibre_channel',  
                'data': {'target_lun': device_number,  
                         'target_discovered': True,  
                         'target_wwn': ports}} 

        LOG.debug(_('Return FC data: %(data)s.')
                  % {'data': data})

        return data

    def terminate_connection(self, volume, connector, **kwargs):
        """Disallow connection from connector."""
        self.common.terminate_connection(volume, connector)

    def extend_volume(self, volume, new_size):
        """Extend an existing EMC(VMAX/VNX) volume."""
        self.common.extend_volume(volume, new_size)

    def get_volume_stats(self, refresh=False):
        """Get volume stats.
        If 'refresh' is True, run update the stats first."""
        if refresh:
            self.update_volume_stats()

        return self._stats

    def update_volume_stats(self):
        """Retrieve stats info from volume group."""
        LOG.debug(_("Updating volume stats"))
        data = self.common.update_volume_stats()
        backend_name = self.configuration.safe_get('volume_backend_name')
        data['volume_backend_name'] = backend_name or 'EMCSMISFCDriver'
        data['storage_protocol'] = 'FC'
        data['driver_version'] = self.VERSION
        self._stats = data
