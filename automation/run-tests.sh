#!/bin/bash -ex

EXEC_PATH=$(dirname "$(realpath "$0")")
PROJECT_PATH="$(dirname $EXEC_PATH)"
EXPORT_DIR="$PWD/exported-artifacts"
CONT_EXPORT_DIR="/exported-artifacts"

CONTAINER_WORKSPACE="/workspace/nmstate"

TEST_TYPE_ALL="all"
TEST_TYPE_FORMAT="format"
TEST_TYPE_LINT="lint"
TEST_TYPE_UNIT_PY36="unit_py36"
TEST_TYPE_UNIT_PY38="unit_py38"
TEST_TYPE_INTEG="integ"
TEST_TYPE_INTEG_TIER1="integ_tier1"
TEST_TYPE_INTEG_TIER2="integ_tier2"
TEST_TYPE_INTEG_SLOW="integ_slow"

FEDORA_IMAGE_DEV="docker.io/nmstate/fedora-nmstate-dev"
CENTOS_IMAGE_DEV="docker.io/nmstate/centos8-nmstate-dev"

PYTEST_OPTIONS="--verbose --verbose \
        --log-level=DEBUG \
        --log-date-format='%Y-%m-%d %H:%M:%S' \
        --log-format='%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s' \
        --durations=5 \
        --cov /usr/lib/python*/site-packages/libnmstate \
        --cov /usr/lib/python*/site-packages/nmstatectl \
        --cov-report=term \
        --log-file=pytest-run.log"

NMSTATE_TEMPDIR=$(mktemp -d /tmp/nmstate-test-XXXX)

: ${CONTAINER_CMD:=podman}

source automation/tests-container-utils.sh
source automation/tests-baremetal-utils.sh

test -t 1 && USE_TTY="-t"

function pyclean {
    exec_cmd '
        find . -type f -name "*.py[co]" -delete
        find . -type d -name "__pycache__" -delete
    '
}

function exec_cmd {
    if [ -z ${RUN_BAREMETAL+x} ];then
        container_exec "$1"
    else
        bash -c "$1"
    fi
}

function dump_network_info {
    exec_cmd '
      nmcli dev; \
      # Use empty PAGER variable to stop nmcli send output to less which hang \
      # the CI. \
      PAGER= nmcli con; \
      ip addr; \
      ip route; \
      cat /etc/resolv.conf; \
      head /proc/sys/net/ipv6/conf/*/disable_ipv6; \
    '
}

function install_nmstate {
    if [ $INSTALL_NMSTATE == "true" ];then
        exec_cmd '
          rpm -ivh `./packaging/make_rpm.sh|tail -1 || exit 1`
        '
    fi
}

function run_tests {
    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_FORMAT ];then
        if [ -z I{$RUN_BAREMETAL+x} ];then
            exec_cmd "tox -e black"
        else
            echo "Running formatter in baremetal is not " \
                 "supported yet"
        fi
    fi

    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_LINT ];then
        if [ -z I{$RUN_BAREMETAL+x} ];then
            exec_cmd "tox -e flake8,pylint"
        else
            echo "Running linter in baremetal is not " \
                 "supported yet"
        fi
    fi

    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_UNIT_PY36 ];then
        if [[ $CONTAINER_IMAGE == *"centos"* ]]; then
            # Due to https://github.com/pypa/virtualenv/issues/1009
            # Instruct virtualenv not to upgrade to the latest versions of pip,
            # setuptools, wheel and etc
            exec_cmd 'env VIRTUALENV_NO_DOWNLOAD=1 \
                            tox --sitepackages -e py36'
        else
            if [ -z I{$RUN_BAREMETAL+x} ];then
                exec_cmd "tox -e py36"
            else
                echo "Running unit test in baremetal is not " \
                     "supported yet"
            fi
        fi
    fi

    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_UNIT_PY38 ];then
        if [[ $CONTAINER_IMAGE == *"centos"* ]]; then
            echo "Running unit test in $CONTAINER_IMAGE container is not " \
                 "support yet"
        else
            if [ -z I{$RUN_BAREMETAL+x} ];then
                exec_cmd "tox -e py38"
            else
                echo "Running unit test in baremetal is not " \
                     "supported yet"
            fi
        fi
    fi

    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_INTEG ];then
        exec_cmd "
          cd $CONTAINER_WORKSPACE &&
          pytest \
            $PYTEST_OPTIONS \
            --cov-report=html:htmlcov-integ \
            tests/integration \
            ${nmstate_pytest_extra_args}"
    fi

    if  [ $TEST_TYPE == $TEST_TYPE_INTEG_TIER1 ];then
        exec_cmd "
          cd $CONTAINER_WORKSPACE &&
          pytest \
            $PYTEST_OPTIONS \
            --cov-report=html:htmlcov-integ_tier1 \
            -m tier1 \
            tests/integration \
            ${nmstate_pytest_extra_args}"
    fi

    if  [ $TEST_TYPE == $TEST_TYPE_INTEG_TIER2 ];then
        exec_cmd "
          cd $CONTAINER_WORKSPACE &&
          pytest \
            $PYTEST_OPTIONS \
            --cov-report=html:htmlcov-integ_tier2 \
            -m tier2 \
            tests/integration \
            ${nmstate_pytest_extra_args}"
    fi

    if [ $TEST_TYPE == $TEST_TYPE_ALL ] || \
       [ $TEST_TYPE == $TEST_TYPE_INTEG_SLOW ];then
        exec_cmd "
          cd $CONTAINER_WORKSPACE &&
          pytest \
            $PYTEST_OPTIONS \
            --cov-report=html:htmlcov-integ_slow \
            -m slow --runslow \
            tests/integration \
            ${nmstate_pytest_extra_args}"
    fi
}

function write_separator {
    set +x
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
    set -x
}

function run_exit {
    write_separator "TEARDOWN"
    dump_network_info
    if [ -z ${RUN_BAREMETAL+x} ];then
        collect_artifacts
        remove_container
        remove_tempdir
    else
        teardown_baremetal_networkenv
    fi
}

function modprobe_ovs {
    lsmod | grep -q ^openvswitch || modprobe openvswitch || { echo 1>&2 "Please run 'modprobe openvswitch' as root"; exit 1; }
}

function check_services {
    exec_cmd 'while ! systemctl is-active dbus; do sleep 1; done'
    exec_cmd 'systemctl start systemd-udevd
                 while ! systemctl is-active systemd-udevd; do sleep 1; done
    '
    exec_cmd '
        systemctl restart NetworkManager
        while ! systemctl is-active NetworkManager; do sleep 1; done
    '
}

options=$(getopt --options "" \
    --long customize:,pytest-args:,help,debug-shell,test-type:,el8,copr:,artifacts-dir:,test-vdsm,baremetal,install-dependencies,use-installed-nmstate\
    -- "${@}")
eval set -- "$options"
while true; do
    case "$1" in
    --pytest-args)
        shift
        nmstate_pytest_extra_args="$1"
        ;;
    --copr)
        shift
        copr_repo="$1"
        ;;
    --customize)
        shift
        customize_cmd="$1"
        ;;
    --debug-shell)
        debug_exit_shell="1"
        ;;
    --test-type)
        shift
        TEST_TYPE="$1"
        ;;
    --el8)
        CONTAINER_IMAGE=$CENTOS_IMAGE_DEV
        ;;
    --artifacts-dir)
        shift
        EXPORT_DIR="$1"
        ;;
    --test-vdsm)
        vdsm_tests
        exit
        ;;
    --baremetal)
        RUN_BAREMETAL="true"
        ;;
    --install-dependencies)
        INSTALL_DEPS="true"
        ;;
    --use-installed-nmstate)
        INSTALL_NMSTATE="false"
        ;;
    --help)
        set +x
        echo -n "$0 [--copr=...] [--customize=...] [--debug-shell] [--el8] "
        echo -n "[--help] [--pytest-args=...] "
        echo "[--test-type=<TEST_TYPE>] [--test-vdsm]"
        echo "    Valid TEST_TYPE are:"
        echo "     * $TEST_TYPE_ALL (default)"
        echo "     * $TEST_TYPE_FORMAT"
        echo "     * $TEST_TYPE_LINT"
        echo "     * $TEST_TYPE_INTEG"
        echo "     * $TEST_TYPE_INTEG_TIER1"
        echo "     * $TEST_TYPE_INTEG_TIER2"
        echo "     * $TEST_TYPE_INTEG_SLOW"
        echo "     * $TEST_TYPE_UNIT_PY36"
        echo "     * $TEST_TYPE_UNIT_PY38"
        echo -n "--customize allows to specify a command to customize the "
        echo "container before running the tests"
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
: ${CONTAINER_IMAGE:=$FEDORA_IMAGE_DEV}
: ${INSTALL_NMSTATE:="true"}
: ${INSTALL_DEPS:="false"}
modprobe_ovs

if [ -z ${RUN_BAREMETAL+x} ];then
    prepare_container_environment
else
    CONTAINER_WORKSPACE="."
    if [ ${INSTALL_DEPS} == "true" ];then
        install_baremetal_dependencies
    fi
        start_baremetal_services
fi

check_services

if [ -z ${RUN_BAREMETAL+x} ];then
    container_add_extra_networks
else
    trap 'run_exit' ERR EXIT
    prepare_baremetal_network
fi

exec_cmd '(source /etc/os-release; echo $PRETTY_NAME); rpm -q NetworkManager'

dump_network_info

pyclean
if [ -z ${RUN_BAREMETAL+x} ];then
    copy_workspace_container
fi

install_nmstate
run_tests
