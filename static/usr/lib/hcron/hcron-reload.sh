#! /bin/bash

echo 'warning: this program name is deprecated in favor of "hcron reload"' 1>&2

exec hcron reload "$@"
