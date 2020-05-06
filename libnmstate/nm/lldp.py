#
# Copyright (c) 2020 Red Hat, Inc.
#
# This file is part of nmstate
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

from libnmstate.nm import connection
from libnmstate.schema import LLDP

from .common import NM


NM_VLAN_ID_KEY = "vid"
NM_VLAN_NAME_KEY = "name"
NM_MACPHY_AUTONEG_KEY = "autoneg"
NM_MACPHY_PMD_AUTONEG_KEY = "pmd-autoneg-cap"
NM_MACPHY_MAU_TYPE_KEY = "operational-mau-type"
NM_PPVLAN_ID_KEY = "ppvid"
NM_PPVLAN_FLAGS_KEY = "flags"
NM_MANAGEMENT_ADDR_KEY = "address"
NM_MANAGEMENT_ADDR_TYPE_KEY = "address-subtype"
NM_MANAGEMENT_ADDR_IFACE_NUMBER_KEY = "interface-number"
NM_MANAGEMENT_ADDR_IFACE_NUMBER_TYPE_KEY = "interface-number-subtype"
NM_MANAGEMENT_ADDR_TYPE_IPV4 = 1
NM_INTERFACE_TYPE_IFINDEX = 2
NM_INTERFACE_TYPE_SYSTEM_PORT = 3
NM_LLDP_STATUS_DEFAULT = -1


LLDP_CAP_NAMES = {
    0b1: LLDP.Neighbors.SYSTEM_CAPABILITY_OTHER,
    0b10: LLDP.Neighbors.SYSTEM_CAPABILITY_REPEATER,
    0b100: LLDP.Neighbors.SYSTEM_CAPABILITY_MAC_BRIDGE,
    0b1000: LLDP.Neighbors.SYSTEM_CAPABILITY_WLAN_AC,
    0b1_0000: LLDP.Neighbors.SYSTEM_CAPABILITY_ROUTER,
    0b10_0000: LLDP.Neighbors.SYSTEM_CAPABILITY_TELEPHONE,
    0b100_0000: LLDP.Neighbors.SYSTEM_CAPABILITY_DOCSIS,
    0b1000_0000: LLDP.Neighbors.SYSTEM_CAPABILITY_STATION,
    0b1_0000_0000: LLDP.Neighbors.SYSTEM_CAPABILITY_CVLAN,
    0b10_0000_0000: LLDP.Neighbors.SYSTEM_CAPABILITY_SVLAN,
    0b100_0000_0000: LLDP.Neighbors.SYSTEM_CAPABILITY_TPMR,
}


LLDP_CHASSIS_TYPE_TO_NMSTATE = [
    LLDP.Neighbors.Chassis.TYPE_RESERVED,
    LLDP.Neighbors.Chassis.TYPE_COMPONENT,
    LLDP.Neighbors.Chassis.TYPE_INTERFACE_ALIAS,
    LLDP.Neighbors.Chassis.TYPE_PORT,
    LLDP.Neighbors.Chassis.TYPE_MAC,
    LLDP.Neighbors.Chassis.TYPE_NETWORK_ADDRESS,
    LLDP.Neighbors.Chassis.TYPE_INTERFACE_NAME,
    LLDP.Neighbors.Chassis.TYPE_LOCAL,
]


LLDP_PORT_TYPE_TO_NMSTATE = [
    LLDP.Neighbors.Port.TYPE_RESERVED,
    LLDP.Neighbors.Port.TYPE_INTERFACE_ALIAS,
    LLDP.Neighbors.Port.TYPE_COMPONENT,
    LLDP.Neighbors.Port.TYPE_MAC,
    LLDP.Neighbors.Port.TYPE_NETWORK_ADDRESS,
    LLDP.Neighbors.Port.TYPE_INTERFACE_NAME,
    LLDP.Neighbors.Port.TYPE_AGENT_CIRCUIT,
    LLDP.Neighbors.Port.TYPE_LOCAL,
]


def apply_lldp_setting(con_setting, iface_desired_state):
    lldp_status = iface_desired_state.get(LLDP.CONFIG_SUBTREE, {}).get(
        LLDP.ENABLED, None
    )
    if lldp_status is not None:
        lldp_status = int(lldp_status)
        con_setting.setting.props.lldp = lldp_status


def get_info(nm_client, nmdev):
    """
    Provides the current LLDP neighbors information
    """
    lldp_status = _get_lldp_status(nm_client, nmdev)
    info = {}
    if lldp_status == NM_LLDP_STATUS_DEFAULT or not lldp_status:
        info[LLDP.ENABLED] = False
    else:
        info[LLDP.ENABLED] = True
        _get_neighbors_info(info, nmdev)

    return {LLDP.CONFIG_SUBTREE: info}


def _get_lldp_status(nm_client, nmdev):
    """
    Default means NM global config file value which is by default disabled.
    According to Beniamino, there is no way from libnm to know if lldp is
    enable or not with libnm if the value in the profile is default.
    Therefore, the best option is to force the users to enable it explicitly.
    This is going to be solved by a property in the NM.Device object to know if
    the device is listening on LLDP.

    Ref: https://bugzilla.redhat.com/1832273
    """
    lldp_status = None
    con_profile = connection.ConnectionProfile(nm_client)
    con_profile.import_by_device(nmdev)
    if con_profile.profile:
        con_setting = con_profile.profile.get_setting_connection()
        if con_setting:
            lldp_status = con_setting.get_lldp()

    return lldp_status


def _get_neighbors_info(info, nmdev):
    neighbors = nmdev.get_lldp_neighbors()
    info_neighbors = []
    for neighbor in neighbors:
        n_info = {}
        _add_neighbor_system_info(neighbor, n_info)
        _add_neighbor_chassis_info(neighbor, n_info)
        _add_neighbor_port_info(neighbor, n_info)
        _add_neighbor_bridge_info(neighbor, n_info)
        _add_neighbor_vlans_info(neighbor, n_info)
        _add_neighbor_macphy_info(neighbor, n_info)
        _add_neighbor_port_vlans_info(neighbor, n_info)
        _add_neighbor_management_addresses(neighbor, n_info)
        info_neighbors.append(n_info)

    if info_neighbors:
        info[LLDP.NEIGHBORS_SUBTREE] = info_neighbors


def _add_neighbor_system_info(neighbor, info):
    sys_name = neighbor.get_attr_value(NM.LLDP_ATTR_SYSTEM_NAME)
    if sys_name:
        info[NM.LLDP_ATTR_SYSTEM_NAME] = sys_name.get_string()

    sys_desc = neighbor.get_attr_value(NM.LLDP_ATTR_SYSTEM_DESCRIPTION)
    if sys_desc:
        info[NM.LLDP_ATTR_SYSTEM_DESCRIPTION] = sys_desc.get_string().rstrip()

    sys_caps = neighbor.get_attr_value(NM.LLDP_ATTR_SYSTEM_CAPABILITIES)
    if sys_caps:
        info[NM.LLDP_ATTR_SYSTEM_CAPABILITIES] = _decode_sys_caps(
            sys_caps.get_uint32()
        )


def _decode_sys_caps(code):
    capabilities = []
    for mask, capability in LLDP_CAP_NAMES.items():
        if code & mask:
            capabilities.append(capability)
    return capabilities


def _add_neighbor_chassis_info(neighbor, info):
    chassis_info = {}
    chassis_id = neighbor.get_attr_value(NM.LLDP_ATTR_CHASSIS_ID)
    if chassis_id:
        chassis_info[NM.LLDP_ATTR_CHASSIS_ID] = chassis_id.get_string()

    chassis_id_type = neighbor.get_attr_value(NM.LLDP_ATTR_CHASSIS_ID_TYPE)
    if chassis_id_type:
        chassis_info[NM.LLDP_ATTR_CHASSIS_ID_TYPE] = _decode_chassis_type(
            chassis_id_type.get_uint32()
        )

    if chassis_info:
        info[LLDP.Neighbors.CHASSIS_SUBTREE] = chassis_info


def _decode_chassis_type(code):
    try:
        return LLDP_CHASSIS_TYPE_TO_NMSTATE[code]
    except IndexError:
        return LLDP.Neighbors.Chassis.TYPE_UNKNOWN


def _add_neighbor_port_info(neighbor, info):
    port_info = {}
    port_id = neighbor.get_attr_value(NM.LLDP_ATTR_PORT_ID)
    if port_id:
        port_info[NM.LLDP_ATTR_PORT_ID] = port_id.get_string()

    port_type = neighbor.get_attr_value(NM.LLDP_ATTR_PORT_ID_TYPE)
    if port_type:
        port_info[NM.LLDP_ATTR_PORT_ID_TYPE] = _decode_port_type(
            port_type.get_uint32()
        )

    if port_info:
        info[LLDP.Neighbors.PORT_SUBTREE] = port_info


def _decode_port_type(code):
    try:
        return LLDP_PORT_TYPE_TO_NMSTATE[code]
    except IndexError:
        return LLDP.Neighbors.Port.TYPE_UNKNOWN


def _add_neighbor_bridge_info(neighbor, info):
    bridge_info = {}
    destination = neighbor.get_attr_value(NM.LLDP_ATTR_DESTINATION)
    if destination:
        info[NM.LLDP_ATTR_DESTINATION] = destination.get_string()

    nearest_bridge = neighbor.get_attr_value(NM.LLDP_DEST_NEAREST_BRIDGE)
    if nearest_bridge:
        bridge_info[NM.LLDP_DEST_NEAREST_BRIDGE] = nearest_bridge.get_string()

    nearest_customer_bridge = neighbor.get_attr_value(
        NM.LLDP_DEST_NEAREST_CUSTOMER_BRIDGE
    )
    if nearest_customer_bridge:
        bridge_info[
            NM.LLDP_DEST_NEAREST_CUSTOMER_BRIDGE
        ] = nearest_customer_bridge.get_string()

    nearest_non_tpmr_bridge = neighbor.get_attr_value(
        NM.LLDP_DEST_NEAREST_NON_TPMR_BRIDGE
    )
    if nearest_non_tpmr_bridge:
        bridge_info[
            NM.LLDP_DEST_NEAREST_NON_TPMR_BRIDGE
        ] = nearest_non_tpmr_bridge.get_string()

    if bridge_info:
        info[LLDP.Neighbors.BRIDGE_SUBTREE] = bridge_info


def _add_neighbor_vlans_info(neighbor, info):
    vlans_info = []
    vlans = neighbor.get_attr_value(NM.LLDP_ATTR_IEEE_802_1_VLANS)
    if vlans:
        vlans = vlans.unpack()
        for vlan in vlans:
            vlan_info = {}
            vlan_info[NM.LLDP_ATTR_IEEE_802_1_VID] = vlan[NM_VLAN_ID_KEY]
            vlan_info[NM.LLDP_ATTR_IEEE_802_1_VLAN_NAME] = vlan[
                NM_VLAN_NAME_KEY
            ].replace("\\000", "")
            if vlan_info:
                vlans_info.append(vlan_info)

        if vlans_info:
            info[LLDP.Neighbors.VLAN_SUBTREE] = vlans


def _add_neighbor_macphy_info(neighbor, info):
    macphy_info = {}
    macphy_conf = neighbor.get_attr_value(NM.LLDP_ATTR_IEEE_802_3_MAC_PHY_CONF)
    if macphy_conf:
        macphy_info[NM_MACPHY_AUTONEG_KEY] = bool(
            macphy_conf[NM_MACPHY_AUTONEG_KEY]
        )
        macphy_info[NM_MACPHY_PMD_AUTONEG_KEY] = macphy_conf[
            NM_MACPHY_PMD_AUTONEG_KEY
        ]
        macphy_info[NM_MACPHY_MAU_TYPE_KEY] = macphy_conf[
            NM_MACPHY_MAU_TYPE_KEY
        ]

        info[LLDP.Neighbors.MAC_PHY_SUBTREE] = macphy_info


def _add_neighbor_port_vlans_info(neighbor, info):
    port_vlans_info = []
    port_vlans = neighbor.get_attr_value(NM.LLDP_ATTR_IEEE_802_1_PPVIDS)
    if port_vlans:
        port_vlans = port_vlans.unpack()
        for p_vlan in port_vlans:
            p_vlan_info = {}
            p_vlan_info[NM_PPVLAN_ID_KEY] = p_vlan[NM_PPVLAN_ID_KEY]
            port_vlans_info.append(p_vlan_info)
        if port_vlans_info:
            info[LLDP.Neighbors.PORT_VLAN_SUBTREE] = port_vlans_info


def _add_neighbor_management_addresses(neighbor, info):
    addresses_info = []
    mngt_addresses = neighbor.get_attr_value(NM.LLDP_ATTR_MANAGEMENT_ADDRESSES)
    if mngt_addresses:
        mngt_addresses = mngt_addresses.unpack()
        for mngt_address in mngt_addresses:
            mngt_address_info = {}
            addr, addr_type = _decode_management_address_type(
                mngt_address[NM_MANAGEMENT_ADDR_TYPE_KEY],
                mngt_address[NM_MANAGEMENT_ADDR_KEY],
            )
            mngt_address_info[NM_MANAGEMENT_ADDR_KEY] = addr
            mngt_address_info[NM_MANAGEMENT_ADDR_TYPE_KEY] = addr_type
            mngt_address_info[
                NM_MANAGEMENT_ADDR_IFACE_NUMBER_KEY
            ] = mngt_address[NM_MANAGEMENT_ADDR_IFACE_NUMBER_KEY]
            mngt_address_info[
                NM_MANAGEMENT_ADDR_IFACE_NUMBER_TYPE_KEY
            ] = _decode_interface_number_type(
                mngt_address[NM_MANAGEMENT_ADDR_IFACE_NUMBER_TYPE_KEY]
            )
            addresses_info.append(mngt_address_info)
        if addresses_info:
            info[LLDP.Neighbors.MANAGEMENT_ADDRESSES_SUBTREE] = addresses_info


def _decode_interface_number_type(code):
    if code == NM_INTERFACE_TYPE_IFINDEX:
        return "ifindex"
    elif code == NM_INTERFACE_TYPE_SYSTEM_PORT:
        return "system-port"
    else:
        return "unknown"


def _decode_management_address_type(code, address):
    if code == NM_MANAGEMENT_ADDR_TYPE_IPV4:
        addr = ".".join(map(str, address))
        addr_type = "ipv4"
    else:
        addr = "::".join(["{:02X}".format(octet) for octet in address])
        addr_type = "ipv6"

    return addr, addr_type
