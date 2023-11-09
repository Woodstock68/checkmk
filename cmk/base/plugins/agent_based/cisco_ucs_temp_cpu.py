#!/usr/bin/env python3
# Copyright (C) 2023 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Mapping, MutableMapping
from typing import Any

from cmk.base.plugins.agent_based.agent_based_api.v1 import register, SNMPTree
from cmk.base.plugins.agent_based.utils.temperature import check_temperature
from cmk.base.plugins.agent_based.utils.temperature import TempParamType as TempParamType

from .agent_based_api.v1 import get_value_store, Service
from .agent_based_api.v1.type_defs import CheckResult, DiscoveryResult, StringTable
from .utils.cisco_ucs import DETECT


def parse_cisco_ucs_temp_cpu(string_table: StringTable) -> dict[str, int]:
    return {name.split("/")[3]: int(temp) for name, temp in string_table}


register.snmp_section(
    name="cisco_ucs_temp_cpu",
    parse_function=parse_cisco_ucs_temp_cpu,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.9.9.719.1.41.2.1",
        oids=[
            "2",  # .1.3.6.1.4.1.9.9.719.1.41.2.1.2  cpu Unit Name
            "10",  # .1.3.6.1.4.1.9.9.719.1.41.2.1.10 cucsProcessorEnvStatsTemperature
        ],
    ),
    detect=DETECT,
)


def discover_cisco_ucs_temp_cpu(section: Mapping[str, int]) -> DiscoveryResult:
    yield from (Service(item=name) for name in section)


def _check_cisco_ucs_temp_cpu(
    item: str,
    params: TempParamType,
    section: Mapping[str, int],
    value_store: MutableMapping[str, Any],
) -> CheckResult:
    if (temperature := section.get(item)) is None:
        return

    yield from check_temperature(
        reading=temperature,
        params=params,
        unique_name=item,
        value_store=value_store,
    )


def check_cisco_ucs_temp_cpu(
    item: str,
    params: TempParamType,
    section: Mapping[str, int],
) -> CheckResult:
    yield from _check_cisco_ucs_temp_cpu(item, params, section, get_value_store())


register.check_plugin(
    name="cisco_ucs_temp_cpu",
    service_name="Temperature CPU %s",
    discovery_function=discover_cisco_ucs_temp_cpu,
    check_function=check_cisco_ucs_temp_cpu,
    check_ruleset_name="temperature",
    check_default_parameters={
        "levels": (75.0, 85.0),
    },
)
