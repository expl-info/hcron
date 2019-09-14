#! /bin/bash

echo 'warning: this program name is deprecated in favor of "hcron run"' 1>&2

exec hcron run "$@"
