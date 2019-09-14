#! /bin/bash

echo 'warning: this program name is deprecated in favor of "hcron conv"' 1>&2

exec hcron conv "$@"
