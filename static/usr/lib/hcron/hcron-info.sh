#! /bin/bash

echo 'warning: this program name is deprecated in favor of "hcron info"' 1>&2

exec hcron info "$@"
