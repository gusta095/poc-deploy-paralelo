# poc-deploy-paralelo

PoC de um modelo de deploy de recursos Azure em "waves": recursos são
agrupados em waves numeradas, todos os recursos de uma wave podem ser
deployados em paralelo, e a wave N+1 só começa depois que a wave N
terminar completamente.

## Requisitos

```bash
pip install pyyaml
```

## Uso

### Listar as waves de um interface.yaml

Lê `./interface.yaml` por padrão e imprime os tipos de recurso agrupados
por wave:

```bash
python3 waves.py
```

```
wave 1 - ['subscriptions']
wave 2 - ['resource_groups']
wave 3 - ['key_vaults', 'managed_identities', 'network_security_groups', 'public_ips', 'route_tables']
wave 4 - ['virtual_networks']
wave 5 - ['cosmos_db_accounts', 'storage_accounts']
wave 6 - ['aks_clusters', 'sql_databases', 'virtual_machines']
```

### Usar um arquivo de interface diferente

```bash
python3 waves.py caminho/para/outro-interface.yaml
```

### Ver o que mudou no último commit

Compara `HEAD~1` com `HEAD` e mostra, além das waves completas, uma linha
`git-diff - [...]` com os tipos de recurso que tiveram alguma instância
adicionada, removida ou alterada no último commit. Funciona tanto local
quanto em CI:

```bash
python3 waves.py --commit
```

```
wave 1 - ['subscriptions']
...

git-diff - ['public_ips', 'storage_accounts']
```

Se não houve mudança no `interface.yaml`, a linha aparece vazia:
`git-diff - []`.

### Ver o que muda em um Pull Request

Compara a branch de destino do PR com `HEAD`. **Só funciona rodando dentro
de uma GitHub Action em um evento `pull_request`**, já que depende da
variável de ambiente `GITHUB_BASE_REF` para saber qual é a branch base —
localmente não tem como simular um PR de verdade:

```bash
python3 waves.py --merge
```

`--commit` e `--merge` são mutuamente exclusivos.

## Arquitetura

O modelo de waves é definido em três lugares que precisam ser mantidos
sincronizados manualmente — não há uma fonte única de verdade:

- `ideia.md` — definição legível do modelo: quais tipos de recurso Azure
  existem e em qual wave cada um entra.
- `interface.yaml` — inventário de exemplo de recursos, agrupados por tipo.
- `waves.py` — implementação: o dict `WAVE_BY_RESOURCE_TYPE` reproduz o
  mesmo mapeamento tipo → wave, e as funções do arquivo agrupam/comparam
  os recursos do `interface.yaml` com base nele.

Ao adicionar um novo tipo de recurso, atualize `ideia.md` e
`WAVE_BY_RESOURCE_TYPE` juntos.
