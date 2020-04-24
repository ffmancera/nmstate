#!/bin/bash -ex

EXEC_PATH=$(dirname "$(realpath "$0")")
PROJECT_PATH="$(dirname $EXEC_PATH)"

TEST_TYPE_ALL="all"
TEST_TYPE_INTEG="integ"
TEST_TYPE_INTEG_TIER1="integ_tier1"
TEST_TYPE_INTEG_TIER2="integ_tier2"
TEST_TYPE_INTEG_SLOW="integ_slow"

PYTEST_OPTIONS="--verbose --verbose \
        --log-level=DEBUG \
        --log-date-format='%Y-%m-%d %H:%M:%S' \
        --log-format='%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s' \
        --durations=5 \
        --cov /usr/lib/python*/site-packages/libnmstate \
        --cov /usr/lib/python*/site-packages/nmstatectl \
        --cov-report=term"

function run_tests {
    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_INTEG ];then
        pytest \
          tests/integration \
          --verbose --verbose \
          ${nmstate_pytest_extra_args}
    fi

    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_INTEG_TIER1 ];then
        pytest \
	  -m tier1 \
          tests/integration \
          --verbose --verbose \
          --log-level=DEBUG \
          ${nmstate_pytest_extra_args}
    fi

    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_INTEG_TIER2 ];then
        pytest \
	  -m tier2 \
          tests/integration \
          --verbose --verbose \
          ${nmstate_pytest_extra_args}
    fi

    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_INTEG_SLOW ];then
        pytest \
	  -m slow --runslow \
          tests/integration \
          --verbose --verbose \
          ${nmstate_pytest_extra_args}
    fi
}

function write_separator {
    local text="$(echo "${1}" | sed 's,., \0,g') "
    local char="="

    local textlength=$(echo -n "${text}" | wc --chars)
    local cols="$(tput cols)"
    local wraplength=$(((cols - textlength) / 2))

    eval printf %.1s "${char}"'{1..'"${wraplength}"\}
    echo -n "${text}"
    wraplength=$((wraplength + ((cols - textlength) % 2)))
    eval printf %.1s "${char}"'{1..'"${wraplength}"\}
    echo
}

function run_exit {
    write_separator "TEARDOWN"
    dump_network_info
}

function modprobe_ovs {
    lsmod | grep -q ^openvswith || modprobe openvswitch || { echo 1>&2 "Please run 'modprobe openvswitch' as root" exit 1; }
}

function check_iface_exist {
    set +e
    ip a s | grep -q $1
}

function prepare_network_environment {
    echo 'ENV{ID_NET_DRIVER}=="veth", ENV{INTERFACE}=="eth[0-9]|eth[0-9]*[0-9]", ENV{NM_UNMANAGED}="0"' >/etc/udev/rules.d/88-veths.rules
    udevadm control --reload-rules
    udevadm settle --timeout=5
    sleep 1

    check_iface_exist 'eth1'
    if [ $? -eq 1 ]; then
        set -e
        ip link add eth1 type veth peer name eth1p
    fi


    check_iface_exist 'eth2'
    if [ $? -eq 1 ]; then
        set -e
        ip link add eth2 type veth peer name eth2p
    fi
}

function teardown_network_environment {
  rm -f /etc/udev/ruled.d/88-veths.rules
  udevadm control --reload-rules
  udevadm settle --timeout=5
  sleep 1

  ip link del eth1
  ip link del eth2
}

function pyclean {
    find . -type f -name "*.py[co]" -delete
    find . -type d -name "__pycache__" -delete
}

options=$(getopt --options "" \
    --long pytest-args:,help,test-type:\
    -- "${@}")
eval set -- "$options"
while true; do
    case "$1" in
    --pytest-args)
        shift
        nmstate_pytest_extra_args="$1"
        ;;
    --test-type)
        shift
        TEST_TYPE="$1"
        ;;
    --help)
        set +x
        echo -n "$0 [--help] [--pytest-args=...] [--test-type=<TEST_TYPE>]"
        echo "    Valid TEST_TYPE are:"
        echo "     * $TEST_TYPE_ALL (default)"
        echo "     * $TEST_TYPE_INTEG"
        echo "     * $TEST_TYPE_INTEG_TIER1"
        echo "     * $TEST_TYPE_INTEG_TIER2"
        echo "     * $TEST_TYPE_INTEG_SLOW"
        set -x
        exit
        ;;
    --)
        shift
        break
        ;;
    esac
    shift
done

: ${TEST_TYPE:=$TEST_TYPE_ALL}

modprobe_ovs

prepare_network_environment

(source /etc/os-release; echo $PRETTY_NAME); rpm -q NetworkManager

pyclean
run_tests

teardown_network_environment
