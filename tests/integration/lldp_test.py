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

from contextlib import contextmanager
import time

import libnmstate
from libnmstate.schema import Interface
from libnmstate.schema import LLDP

from .testlib import assertlib
from .testlib import cmdlib
from .testlib import statelib


ETH1 = "eth1"

LLDP_SYSTEM_DESC = (
    "Summit300-48 - Version 7.4e.1 (Build 5) by Release_Master "
    "05/27/05 04:53:11"
)

LLDP_CAPS = ["mac-bridge", "router"]


def test_enable_lldp(eth1_up):
    with lldp_enabled(eth1_up) as dstate:
        assertlib.assert_state_match(dstate)


def test_lldp_system(eth1_up):
    with lldp_enabled(eth1_up):
        _send_lldp_packet()
        dstate = statelib.show_only((ETH1,))
        lldp_config = dstate[Interface.KEY][0][LLDP.CONFIG_SUBTREE]
        test_neighbor = _get_lldp_test(lldp_config[LLDP.NEIGHBORS_SUBTREE])

        assert test_neighbor["system-name"] == "Summit300-48"
        assert test_neighbor["system-description"] == LLDP_SYSTEM_DESC
        assert test_neighbor["system-capabilities"] == LLDP_CAPS


def test_lldp_chassis(eth1_up):
    with lldp_enabled(eth1_up):
        _send_lldp_packet()
        dstate = statelib.show_only((ETH1,))
        lldp_config = dstate[Interface.KEY][0][LLDP.CONFIG_SUBTREE]
        test_neighbor = _get_lldp_test(lldp_config[LLDP.NEIGHBORS_SUBTREE])
        test_chassis = test_neighbor[LLDP.Neighbors.CHASSIS_SUBTREE]

        assert test_chassis["chassis-id"] == "00:01:30:F9:AD:A0"
        assert test_chassis["chassis-id-type"] == "mac"


def test_lldp_destination(eth1_up):
    with lldp_enabled(eth1_up):
        _send_lldp_packet()
        dstate = statelib.show_only((ETH1,))
        lldp_config = dstate[Interface.KEY][0][LLDP.CONFIG_SUBTREE]
        test_neighbor = _get_lldp_test(lldp_config[LLDP.NEIGHBORS_SUBTREE])

        assert test_neighbor["destination"] == "nearest-bridge"


def test_lldp_management_addresses(eth1_up):
    with lldp_enabled(eth1_up):
        _send_lldp_packet()
        dstate = statelib.show_only((ETH1,))
        lldp_config = dstate[Interface.KEY][0][LLDP.CONFIG_SUBTREE]
        test_neigh = _get_lldp_test(lldp_config[LLDP.NEIGHBORS_SUBTREE])
        test_mngt = test_neigh[LLDP.Neighbors.MANAGEMENT_ADDRESSES_SUBTREE][0]

        assert test_mngt["address"] == "00::01::30::F9::AD::A0"
        assert test_mngt["address-subtype"] == "ipv6"
        assert test_mngt["interface-number"] == 1001
        assert test_mngt["interface-number-subtype"] == "ifindex"


def test_lldp_macphy(eth1_up):
    with lldp_enabled(eth1_up):
        _send_lldp_packet()
        dstate = statelib.show_only((ETH1,))
        lldp_config = dstate[Interface.KEY][0][LLDP.CONFIG_SUBTREE]
        test_neighbor = _get_lldp_test(lldp_config[LLDP.NEIGHBORS_SUBTREE])
        test_macphy = test_neighbor[LLDP.Neighbors.MAC_PHY_SUBTREE]

        assert test_macphy["autoneg"] is True
        assert test_macphy["operational-mau-type"] == 16
        assert test_macphy["pmd-autoneg-cap"] == 27648


def test_lldp_port(eth1_up):
    with lldp_enabled(eth1_up):
        _send_lldp_packet()
        dstate = statelib.show_only((ETH1,))
        lldp_config = dstate[Interface.KEY][0][LLDP.CONFIG_SUBTREE]
        test_neighbor = _get_lldp_test(lldp_config[LLDP.NEIGHBORS_SUBTREE])
        test_port = test_neighbor[LLDP.Neighbors.PORT_SUBTREE]

        assert test_port["port-id"] == "1/1"
        assert test_port["port-id-type"] == "interface-name"


def test_lldp_port_vlan(eth1_up):
    with lldp_enabled(eth1_up):
        _send_lldp_packet()
        dstate = statelib.show_only((ETH1,))
        lldp_config = dstate[Interface.KEY][0][LLDP.CONFIG_SUBTREE]
        test_neighbor = _get_lldp_test(lldp_config[LLDP.NEIGHBORS_SUBTREE])
        test_portv = test_neighbor[LLDP.Neighbors.PORT_VLAN_SUBTREE][0]

        assert test_portv["ppvid"] == 0


def test_lldp_vlan(eth1_up):
    with lldp_enabled(eth1_up):
        _send_lldp_packet()
        dstate = statelib.show_only((ETH1,))
        lldp_config = dstate[Interface.KEY][0][LLDP.CONFIG_SUBTREE]
        test_neighbor = _get_lldp_test(lldp_config[LLDP.NEIGHBORS_SUBTREE])
        test_vlan = test_neighbor[LLDP.Neighbors.VLAN_SUBTREE][0]

        assert test_vlan["name"] == "v2-0488-03-0505\\000"


@contextmanager
def lldp_enabled(ifstate):
    lldp_config = ifstate[Interface.KEY][0][LLDP.CONFIG_SUBTREE]
    lldp_config[LLDP.ENABLED] = True
    libnmstate.apply(ifstate)
    try:
        yield ifstate
    finally:
        lldp_config[LLDP.ENABLED] = False
        libnmstate.apply(ifstate)


def _send_lldp_packet():
    cmdlib.exec_cmd(
        (
            "tcpreplay",
            "--intf1=eth1peer",
            "tests/integration/test_captures/lldp.pcap",
        ),
        check=True,
    )
    time.sleep(1)


def _get_lldp_test(neighbors):
    selected_neighbor = None
    for neighbor in neighbors:
        if neighbor["system-name"] == "Summit300-48":
            selected_neighbor = neighbor

    return selected_neighbor
