#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.gui.cron import register_job

from ._manager import execute_housekeeping_job


def register() -> None:
    register_job(execute_housekeeping_job)
