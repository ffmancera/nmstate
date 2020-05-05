VETH_ETH1_CREATED="false"
VETH_ETH2_CREATED="false"

function check_iface_exist {
    ip a s | grep -q $1
}

function prepare_baremetal_network {
    echo 'ENV{ID_NET_DRIVER}=="veth", ENV{INTERFACE}=="eth[0-9]|eth[0-9]*[0-9]", ENV{NM_UNMANAGED}="0"' >/etc/udev/rules.d/88-veths.rules
    udevadm control --reload-rules
    udevadm settle --timeout=5
    sleep 1

    set +e
    check_iface_exist 'eth1'
    if [ $? -eq 1 ]; then
        VETH_ETH1_CREATED="yes"
        ip link add eth1 type veth peer name eth1p && ip link set dev eth1p up
    fi

    check_iface_exist 'eth2'
    if [ $? -eq 1 ]; then
        VETH_ETH2_CREATED="yes"
        ip link add eth2 type veth peer name eth2p && ip link set dev eth2p up
    fi
    set -e
}

function teardown_baremetal_networkenv {
    rm -f /etc/udev/ruled.d/88-veths.rules
    udevadm control --reload-rules
    udevadm settle --timeout=5
    sleep 1
    if [ $VETH_ETH1_CREATED == "yes" ]; then
        ip link del eth1
    fi

    if [ $VETH_ETH2_CREATED == "yes" ]; then
        ip link del eth2
    fi
}

function install_baremetal_dependencies {
    dnf install -y NetworkManager-ovs NetworkManager-team
    pip3 install pytest pytest-cov
}

function start_baremetal_services {
    systemctl start openvswitch
    systemctl restart NetworkManager
}
