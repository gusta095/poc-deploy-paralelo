#!/usr/bin/env python3
"""Separa recursos Azure do interface.yaml em waves de deploy."""

import argparse
import os
import subprocess
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
    """Carrega e retorna o interface YAML como dict."""
    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data or {}

def group_by_wave(interface):
    """Agrupa os tipos de recurso presentes no interface em waves.

    Retorna um dict mapeando o numero da wave para uma lista ordenada das
    chaves de tipo de recurso (ex: "storage_accounts"), sem repeticao por wave.
    """
    waves = {}
    for resource_type, resources in interface.items():
        wave = WAVE_BY_RESOURCE_TYPE.get(resource_type)
        if wave is None:
            print(f"aviso: tipo de recurso desconhecido: {resource_type}", file=sys.stderr)
            continue
        if resources:
            waves.setdefault(wave, set()).add(resource_type)

    return {wave: sorted(resource_types) for wave, resource_types in waves.items()}

def print_waves(waves):
    """Imprime cada wave e suas chaves de recurso, em ordem de wave."""
    for wave in sorted(waves):
        print(f"wave {wave} - {waves[wave]}")

def load_interface_at_ref(ref, path):
    """Carrega o interface YAML como ele existia em um git ref especifico.

    Roda `git show <ref>:<path>` para que o diff compare estados
    commitados sem tocar na working tree. Encerra com uma mensagem de
    erro no stderr se o git nao conseguir resolver o ref/path.
    """
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"erro: nao foi possivel ler {path} em '{ref}': {result.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)
    return yaml.safe_load(result.stdout) or {}

def flatten_instances(interface):
    """Mapeia cada chave de instancia de recurso ao seu (resource_type, value)."""
    flat = {}
    for resource_type, resources in interface.items():
        for resource_key, value in (resources or {}).items():
            flat[resource_key] = (resource_type, value)
    return flat

def diff_changed_keys(old_interface, new_interface):
    """Retorna o conjunto de chaves de instancia adicionadas, removidas ou alteradas entre dois estados."""
    old_flat = flatten_instances(old_interface)
    new_flat = flatten_instances(new_interface)
    all_keys = set(old_flat) | set(new_flat)
    return {key for key in all_keys if old_flat.get(key) != new_flat.get(key)}

def group_changed_by_wave(old_interface, new_interface):
    """Agrupa em waves os tipos de recurso com instancias alteradas, no mesmo formato de group_by_wave()."""
    old_flat = flatten_instances(old_interface)
    new_flat = flatten_instances(new_interface)
    changed_keys = diff_changed_keys(old_interface, new_interface)

    waves = {}
    for resource_key in changed_keys:
        resource_type, _ = new_flat.get(resource_key) or old_flat[resource_key]
        wave = WAVE_BY_RESOURCE_TYPE.get(resource_type)
        if wave is None:
            print(f"aviso: tipo de recurso desconhecido: {resource_type}", file=sys.stderr)
            continue
        waves.setdefault(wave, set()).add(resource_type)

    return {wave: sorted(resource_types) for wave, resource_types in waves.items()}

def resolve_diff_refs(args):
    """Define o par (old_ref, new_ref) a comparar, com base em --commit/--merge."""
    if args.commit:
        return "HEAD~1", "HEAD"

    if args.merge:
        base_ref = os.environ.get("GITHUB_BASE_REF")
        if not base_ref:
            print(
                "erro: --merge so funciona dentro de uma GitHub Action num evento "
                "pull_request (variavel GITHUB_BASE_REF nao encontrada)",
                file=sys.stderr,
            )
            sys.exit(1)
        return base_ref, "HEAD"

    return None

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "interface_file",
        nargs="?",
        default="interface.yaml",
        type=Path,
        help="caminho para o arquivo interface.yaml (padrao: ./interface.yaml)",
    )
    diff_group = parser.add_mutually_exclusive_group()
    diff_group.add_argument(
        "--commit",
        action="store_true",
        help="mostra tambem os recursos alterados entre HEAD~1 e HEAD",
    )
    diff_group.add_argument(
        "--merge",
        action="store_true",
        help=(
            "mostra tambem os recursos alterados entre a branch base do PR "
            "(GITHUB_BASE_REF) e HEAD; so funciona rodando numa GitHub Action"
        ),
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

    refs = resolve_diff_refs(args)
    if refs is not None:
        old_ref, new_ref = refs
        old_interface = load_interface_at_ref(old_ref, args.interface_file)
        new_interface = load_interface_at_ref(new_ref, args.interface_file)
        changed_waves = group_changed_by_wave(old_interface, new_interface)
        print()
        print("alterado:")
        if changed_waves:
            print_waves(changed_waves)
        else:
            print("(nenhuma mudanca)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
