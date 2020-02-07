#!/usr/bin/env python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2014             mk@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is part of Check_MK.
# The official homepage is at http://mathias-kettner.de/check_mk.
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# tails. You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.
"""Check_MK Special agent to monitor JMX using Mbeans exposed by jolokia
"""
import os
import sys
import argparse
from cmk.special_agents.utils import vcrtrace

# TODO: is there a better way to do this?
import cmk.utils.paths
sys.path.append(str(cmk.utils.paths.local_agents_dir / 'plugins'))
sys.path.append(os.path.join(cmk.utils.paths.agents_dir, 'plugins'))
import mk_jolokia  # type:ignore  # pylint: disable=import-error,wrong-import-position


def parse_arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-v", "--verbose", action="count", help='''Verbose mode''')
    parser.add_argument("--debug",
                        action="store_true",
                        help="Debug mode: let python exceptions come through")
    parser.add_argument("--vcrtrace",
                        action=vcrtrace(**mk_jolokia.JolokiaInstance.FILTER_SENSITIVE))

    opts_with_help = (t for t in mk_jolokia.DEFAULT_CONFIG_TUPLES if len(t) == 3)

    for key, default, help_str in opts_with_help:
        if default is not None:
            help_str += " Default: %s" % default

        parser.add_argument("--%s" % key, default=default, help=help_str)

    # now add some arguments we cannot define in the way above:
    parser.add_argument("--no-cert-check",
                        action="store_true",
                        help='''Skip SSL certificate verification (not recommended)''')

    return parser.parse_args(argv)


def main(sys_argv=None):
    if sys_argv is None:
        sys_argv = sys.argv[1:]

    args = parse_arguments(sys_argv)
    config = mk_jolokia.get_default_config_dict()

    if args.no_cert_check:
        config["verify"] = False

    for key in config:
        if hasattr(args, key):
            config[key] = getattr(args, key)

    instance = mk_jolokia.JolokiaInstance(config)
    try:
        mk_jolokia.query_instance(instance)
    except mk_jolokia.SkipInstance:
        pass
