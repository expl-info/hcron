#! /bin/bash

echo 'warning: this program name is deprecated in favor of "hcron event"' 1>&2

exec hcron event "$@"
