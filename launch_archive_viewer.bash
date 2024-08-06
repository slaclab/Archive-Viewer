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
ARGS=""

while [ $# -gt 0 ]
do
    case $1 in
        -m | --macros) MACROS="$2"
                       shift ;;
        *) ARGS+="$1 " ;;
    esac
    shift
done

echo $@

pydm --hide-nav-bar --hide-status-bar \
    -m "$MACROS" \
    archive_viewer.py "$ARGS"

exit 0
