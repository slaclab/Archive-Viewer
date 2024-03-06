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

pydm --hide-nav-bar --hide-status-bar --hide-menu-bar \
    archive_viewer.py

exit 0