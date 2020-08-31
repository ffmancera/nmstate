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

from contextlib import contextmanager

from libnmstate import nm
from libnmstate.nm.common import NM
from libnmstate.schema import Interface
from libnmstate.schema import VLAN

from ..testlib.retry import retry_till_true_or_timeout
from ..testlib import statelib
from .testlib import main_context


ETH1 = "eth1"

RETRY_TIMEOUT = 5


def test_create_and_remove_vlan(nm_plugin, eth1_up):
    vlan_desired_state = {
        VLAN.CONFIG_SUBTREE: {VLAN.ID: 101, VLAN.BASE_IFACE: ETH1}
    }

    with _vlan_interface(nm_plugin.context, vlan_desired_state):
        vlan_current_state = _get_vlan_current_state(vlan_desired_state)
        assert vlan_desired_state == vlan_current_state

    assert retry_till_true_or_timeout(5, _vlan_is_absent, vlan_desired_state)


def _vlan_is_absent(vlan_desired_state):
    return not _get_vlan_current_state(vlan_desired_state)


@contextmanager
def _vlan_interface(ctx, state):
    profile = None
    try:
        profile = _create_vlan(ctx, state)
        yield
    finally:
        _delete_vlan(ctx, profile)


def _get_vlan_current_state(vlan_desired_state):
    ifname = _get_vlan_ifname(vlan_desired_state)
    state = statelib.show_only((ifname,))
    vlan_state = {}
    if state[Interface.KEY]:
        iface_state = state[Interface.KEY][0]
        vlan_state = {VLAN.CONFIG_SUBTREE: iface_state[VLAN.CONFIG_SUBTREE]}

    return vlan_state


def _create_vlan(ctx, vlan_desired_state):
    ifname = _get_vlan_ifname(vlan_desired_state)
    con_setting = nm.connection.ConnectionSetting()
    con_setting.create(
        con_name=ifname,
        iface_name=ifname,
        iface_type=NM.SETTING_VLAN_SETTING_NAME,
    )
    vlan_setting = nm.vlan.create_setting(
        vlan_desired_state, base_con_profile=None
    )
    ipv4_setting = nm.ipv4.create_setting({}, None)
    ipv6_setting = nm.ipv6.create_setting({}, None)
    with main_context(ctx):
        con_profile = nm.profile.NmProfile(ctx, True)
        con_profile._simple_conn = nm.connection.create_new_simple_connection(
            (con_setting.setting, vlan_setting, ipv4_setting, ipv6_setting)
        )
        con_profile._add()
        ctx.wait_all_finish()
        con_profile.activate()
        ctx.wait_all_finish()
        return con_profile


def _get_vlan_ifname(state):
    return (
        state[VLAN.CONFIG_SUBTREE][VLAN.BASE_IFACE]
        + "."
        + str(state[VLAN.CONFIG_SUBTREE][VLAN.ID])
    )


def _delete_vlan(ctx, profile):
    with main_context(ctx):
        if profile:
            nm.device.deactivate(ctx, profile.nmdev)
            ctx.wait_all_finish()
            profile.delete()
