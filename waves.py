#!/usr/bin/env python3
"""Split Azure resources from interface.yaml into deployment waves."""

import argparse
import sys
from pathlib import Path

import yaml

WAVE_BY_RESOURCE_TYPE = {
    "subscriptions": 1,
    "resource_groups": 2,
    "network_security_groups": 3,
    "route_tables": 3,
    "public_ips": 3,
    "key_vaults": 3,
    "log_analytics_workspaces": 3,
    "managed_identities": 3,
    "managed_disks": 3,
    "private_dns_zones": 3,
    "firewall_policies": 3,
    "virtual_networks": 4,
    "application_insights": 4,
    "nat_gateways": 4,
    "network_interfaces": 5,
    "app_service_plans": 5,
    "storage_accounts": 5,
    "container_registries": 5,
    "private_dns_zone_vnet_links": 5,
    "firewalls": 5,
    "bastion_hosts": 5,
    "cosmos_db_accounts": 5,
    "sql_servers": 5,
    "container_apps_environments": 5,
    "virtual_machines": 6,
    "function_apps": 6,
    "private_endpoints": 6,
    "sql_databases": 6,
    "container_apps": 6,
    "aks_clusters": 6,
}


def load_interface(path):
    """Load and return the interface YAML as a dict."""
    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data or {}


def group_by_wave(interface):
    """Group resource keys from the interface into waves.

    Returns a dict mapping wave number to a sorted list of resource keys.
    """
    waves = {}
    for resource_type, resources in interface.items():
        wave = WAVE_BY_RESOURCE_TYPE.get(resource_type)
        if wave is None:
            print(f"aviso: tipo de recurso desconhecido: {resource_type}", file=sys.stderr)
            continue
        for resource_key in (resources or {}):
            waves.setdefault(wave, []).append(resource_key)

    for resource_keys in waves.values():
        resource_keys.sort()

    return waves


def print_waves(waves):
    """Print each wave and its resource keys, in wave order."""
    for wave in sorted(waves):
        print(f"wave {wave} - {waves[wave]}")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "interface_file",
        nargs="?",
        default="interface.yaml",
        type=Path,
        help="caminho para o arquivo interface.yaml (padrao: ./interface.yaml)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.interface_file.exists():
        print(f"erro: arquivo nao encontrado: {args.interface_file}", file=sys.stderr)
        return 1

    interface = load_interface(args.interface_file)
    waves = group_by_wave(interface)
    print_waves(waves)
    return 0


if __name__ == "__main__":
    sys.exit(main())
