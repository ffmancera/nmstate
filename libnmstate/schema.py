#
# Copyright (c) 2018-2020 Red Hat, Inc.
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

import pkgutil
import yaml


def load(schema_name):
    return yaml.load(
        pkgutil.get_data("libnmstate", "schemas/" + schema_name + ".yaml"),
        Loader=yaml.SafeLoader,
    )


ifaces_schema = load("operational-state")


class Interface:
    KEY = "interfaces"

    NAME = "name"
    TYPE = "type"
    STATE = "state"
    DESCRIPTION = "description"

    IPV4 = "ipv4"
    IPV6 = "ipv6"

    MAC = "mac-address"
    MTU = "mtu"


class Route:
    KEY = "routes"

    RUNNING = "running"
    CONFIG = "config"
    STATE = "state"
    STATE_ABSENT = "absent"
    TABLE_ID = "table-id"
    DESTINATION = "destination"
    NEXT_HOP_INTERFACE = "next-hop-interface"
    NEXT_HOP_ADDRESS = "next-hop-address"
    METRIC = "metric"
    USE_DEFAULT_METRIC = -1
    USE_DEFAULT_ROUTE_TABLE = 0


class RouteRule:
    KEY = "route-rules"
    CONFIG = "config"
    IP_FROM = "ip-from"
    IP_TO = "ip-to"
    PRIORITY = "priority"
    ROUTE_TABLE = "route-table"
    USE_DEFAULT_PRIORITY = -1
    USE_DEFAULT_ROUTE_TABLE = 0


class DNS:
    KEY = "dns-resolver"
    RUNNING = "running"
    CONFIG = "config"
    SERVER = "server"
    SEARCH = "search"


class Constants:
    INTERFACES = Interface.KEY
    ROUTES = Route.KEY
    DNS = DNS.KEY


class InterfaceState:
    KEY = Interface.STATE

    DOWN = "down"
    UP = "up"
    ABSENT = "absent"


class InterfaceType:
    KEY = Interface.TYPE

    BOND = "bond"
    DUMMY = "dummy"
    ETHERNET = "ethernet"
    LINUX_BRIDGE = "linux-bridge"
    OVS_BRIDGE = "ovs-bridge"
    OVS_INTERFACE = "ovs-interface"
    OVS_PORT = "ovs-port"
    UNKNOWN = "unknown"
    VLAN = "vlan"
    VXLAN = "vxlan"
    TEAM = "team"

    VIRT_TYPES = (
        BOND,
        DUMMY,
        LINUX_BRIDGE,
        OVS_BRIDGE,
        OVS_PORT,
        OVS_INTERFACE,
        TEAM,
        VLAN,
        VXLAN,
    )


class InterfaceIP:
    ENABLED = "enabled"
    ADDRESS = "address"
    ADDRESS_IP = "ip"
    ADDRESS_PREFIX_LENGTH = "prefix-length"
    DHCP = "dhcp"
    AUTO_DNS = "auto-dns"
    AUTO_GATEWAY = "auto-gateway"
    AUTO_ROUTES = "auto-routes"


class InterfaceIPv4(InterfaceIP):
    pass


class InterfaceIPv6(InterfaceIP):
    AUTOCONF = "autoconf"


class Bond:
    KEY = InterfaceType.BOND
    CONFIG_SUBTREE = "link-aggregation"

    MODE = "mode"
    SLAVES = "slaves"
    OPTIONS_SUBTREE = "options"


class BondMode:
    ROUND_ROBIN = "balance-rr"
    ACTIVE_BACKUP = "active-backup"
    XOR = "balance-xor"
    BROADCAST = "broadcast"
    LACP = "802.3ad"
    TLB = "balance-tlb"
    ALB = "balance-alb"


class Bridge:
    CONFIG_SUBTREE = "bridge"
    OPTIONS_SUBTREE = "options"
    PORT_SUBTREE = "port"

    class Port:
        NAME = "name"
        VLAN_SUBTREE = "vlan"

        class Vlan:
            ENABLE_NATIVE = "enable-native"
            TRUNK_TAGS = "trunk-tags"
            MODE = "mode"
            TAG = "tag"

            class Mode:
                ACCESS = "access"
                TRUNK = "trunk"
                UNKNOWN = "unknown"

            class TrunkTags:
                ID = "id"
                ID_RANGE = "id-range"
                MIN_RANGE = "min"
                MAX_RANGE = "max"


class LinuxBridge(Bridge):
    TYPE = "linux-bridge"
    STP_SUBTREE = "stp"

    class Options:
        GROUP_FORWARD_MASK = "group-forward-mask"
        MAC_AGEING_TIME = "mac-ageing-time"
        MULTICAST_SNOOPING = "multicast-snooping"

    class Port(Bridge.Port):
        STP_HAIRPIN_MODE = "stp-hairpin-mode"
        STP_PATH_COST = "stp-path-cost"
        STP_PRIORITY = "stp-priority"

    class STP:
        ENABLED = "enabled"
        FORWARD_DELAY = "forward-delay"
        HELLO_TIME = "hello-time"
        MAX_AGE = "max-age"
        PRIORITY = "priority"


class Ethernet:
    TYPE = InterfaceType.ETHERNET
    CONFIG_SUBTREE = "ethernet"

    AUTO_NEGOTIATION = "auto-negotiation"
    SPEED = "speed"
    DUPLEX = "duplex"

    FULL_DUPLEX = "full"
    HALF_DUPLEX = "half"

    SRIOV_SUBTREE = "sr-iov"

    class SRIOV:
        TOTAL_VFS = "total-vfs"
        VFS_SUBTREE = "vfs"

        class VFS:
            ID = "id"
            MAC_ADDRESS = "mac-address"
            SPOOF_CHECK = "spoof-check"
            TRUST = "trust"
            MIN_TX_RATE = "min-tx-rate"
            MAX_TX_RATE = "max-tx-rate"


class VLAN:
    TYPE = InterfaceType.VLAN
    CONFIG_SUBTREE = "vlan"

    ID = "id"
    BASE_IFACE = "base-iface"


class VXLAN:
    TYPE = InterfaceType.VXLAN
    CONFIG_SUBTREE = "vxlan"

    ID = "id"
    BASE_IFACE = "base-iface"
    REMOTE = "remote"
    DESTINATION_PORT = "destination-port"


class OVSBridge(Bridge):
    TYPE = "ovs-bridge"

    class Options:
        FAIL_MODE = "fail-mode"
        MCAST_SNOOPING_ENABLED = "mcast-snooping-enable"
        RSTP = "rstp"
        STP = "stp"

    class Port(Bridge.Port):
        LINK_AGGREGATION_SUBTREE = "link-aggregation"

        class LinkAggregation:
            MODE = "mode"
            SLAVES_SUBTREE = "slaves"

            class Slave:
                NAME = "name"

            class Options:
                DOWN_DELAY = "bond-downdelay"
                UP_DELAY = "bond-updelay"

            class Mode:
                ACTIVE_BACKUP = "active-backup"
                BALANCE_SLB = "balance-slb"
                BALANCE_TCP = "balance-tcp"
                LACP = "lacp"


class Team:
    TYPE = InterfaceType.TEAM
    CONFIG_SUBTREE = InterfaceType.TEAM

    PORT_SUBTREE = "ports"
    RUNNER_SUBTREE = "runner"

    class Port:
        NAME = "name"

    class Runner:
        NAME = "name"

        class RunnerMode:
            LOAD_BALANCE = "loadbalance"


class LLDP:
    CONFIG_SUBTREE = "lldp"
    ENABLED = "enabled"
    NEIGHBORS_SUBTREE = "neighbors"

    class Neighbors:
        SYSTEM_CAPABILITY_OTHER = "other"
        SYSTEM_CAPABILITY_REPEATER = "repeater"
        SYSTEM_CAPABILITY_MAC_BRIDGE = "mac-bridge"
        SYSTEM_CAPABILITY_WLAN_AC = "wlan-access-point"
        SYSTEM_CAPABILITY_ROUTER = "router"
        SYSTEM_CAPABILITY_TELEPHONE = "telephone"
        SYSTEM_CAPABILITY_DOCSIS = "docsis"
        SYSTEM_CAPABILITY_STATION = "station-only"
        SYSTEM_CAPABILITY_CVLAN = "c-vlan"
        SYSTEM_CAPABILITY_SVLAN = "s-vlan"
        SYSTEM_CAPABILITY_TPMR = "tpmr"

        CHASSIS_SUBTREE = "chassis"

        class Chassis:
            TYPE_RESERVED = "reserved"
            TYPE_COMPONENT = "component"
            TYPE_INTERFACE_ALIAS = "interface-alias"
            TYPE_PORT = "port"
            TYPE_MAC = "mac"
            TYPE_NETWORK_ADDRESS = "network-address"
            TYPE_INTERFACE_NAME = "interface-name"
            TYPE_LOCAL = "local"
            TYPE_UNKNOWN = "unknown"

        PORT_SUBTREE = "port"

        class Port:
            TYPE_RESERVED = "reserved"
            TYPE_INTERFACE_ALIAS = "interface-alias"
            TYPE_COMPONENT = "component"
            TYPE_MAC = "mac"
            TYPE_NETWORK_ADDRESS = "network-address"
            TYPE_INTERFACE_NAME = "interface-name"
            TYPE_AGENT_CIRCUIT = "agent-circuit"
            TYPE_LOCAL = "local"
            TYPE_UNKNOWN = "unknown"

        VLAN_SUBTREE = "vlan"
        MAC_PHY_SUBTREE = "mac-phy"
        PORT_VLAN_SUBTREE = "port-vlan"
        MANAGEMENT_ADDRESSES_SUBTREE = "management-addresses"
        BRIDGE_SUBTREE = "bridge"
