#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")/archive_viewer/"

usage(){
    echo "PyDM Archive Viewer"
    echo "Usage:" 1>&2
    echo "  launch_archive_viewer.bash" 1>&2
}
exit_abnormal(){
    usage
    exit 1
}

MACROS=""
IMPORT_FILE=""

while [ $# -gt 0 ]
do
    case $1 in
        -m | --macros) MACROS="$2"
                       shift ;;
        -i | --import) IMPORT_FILE="$2"
                       shift ;;
        -h | --help) exit_abnormal ;;
        *) exit_abnormal
    esac
    shift
done

pydm --hide-nav-bar --hide-status-bar \
    -m "MACROS" \
    archive_viewer.py

exit 0
