# Auto-Aim Memory Discovery v1 — controlled byte differences

**Important:** This is a discovery utility, not the production memory adapter. It requires operator confirmation of the **emulator's loaded ROM identity and N64 core**, selection of the memory domain by exact name, and observed domain size. There is no assumed address, offset, pointer or auto-aim field.

## Preparation

1. Stop the auto-aim observer and other Lua scripts. Save game state if necessary.
2. `python .\tools\prepare_output.py`
3. In BizHawk, load the intended GoldenEye ROM and note core, region/revision and verifiable ROM hash outside this tool.
4. Open `autoaim_memory_discovery_v1.lua` from the repository root. Its first run prints all available memory domains and sizes and **does not read or dump any bytes**.
5. Inspect the list. In this script, set **both** `DOMAIN` (the exact observed RAM-domain string) and `EXPECTED_SIZE` (the observed byte count). The module refuses domains larger than 8 MiB, or unexpected sizes. Run again. Never assume that domain offset equals virtual/physical RDRAM address. If no suitable verified RAM domain exists, stop the experiment.

## Experiment (operator-confirmed)

Use an equivalent game state for all three captures. Keep camera, weapon, target, and player position constant. For A1 confirm auto-aim enabled, then:
```powershell
python .\tools\send_autoaim_mem_v1.py A1
```
Check the BizHawk log for `captured A1` and ensure `output/csv/autoaim_mem_v1_manifest.csv` contains the capture. Change **only** auto-aim setting to disabled, restore an equivalent scene, then capture `B`. Re-enable and capture `A2`. One command at a time, confirming each capture.

```powershell
python .\tools\send_autoaim_mem_v1.py B
python .\tools\send_autoaim_mem_v1.py A2
python .\tools\analyze_autoaim_mem_v1.py
```

The helper emits *requests* only; a success message from Python is not confirmation of capture. The Lua collector writes raw data to `output/archive` and a CSV manifest to `output/csv`. Dumping may stall the emulator briefly. Do not publish raw snapshots without checking for private or copyrighted content.

## Interpretation

Analyzer computes raw offsets for which byte(A1) == byte(A2) and byte(A1) != byte(B). These are **unverified correlated candidates** and may include menu state, timers, nearby gameplay changes or noise. They are not stable symbols. Check repeatability across new sessions, positive/negative controls, data width, endianity, domain and ROM hash before any candidate enters `GoldenEye.mapping`.

No memory writes. Do not fill in `catalog/symbols.json` from these candidate results.

## Important limitations

- This v1 method cannot deduce auto-aim target coordinates or validate causal behavior.
- `memory.read_u8`, `memory.getmemorydomainlist`, `memory.getmemorydomainsize` must be supported by the selected BizHawk core.
- Data belongs to emulator domain offsets, not automatically game addresses.
- The first run aborts after displaying domain metadata by design; only a deliberate script edit opts into collection.

## Resultado executado — 23/10/2026 (A/B/A RDRAM)

O operador confirmou a execução de uma sessão experimental de leitura da memória, com os seguintes fatos:

| Snapshot | Configuração declarada | Frame | Bytes | Manifesto |
|---|---|---:|---:|---|
| A1 | auto-aim ligado | 41691 | 8388608 | confirmado |
| B | auto-aim desligado | 51170 | 8388608 | confirmado |
| A2 | auto-aim religado | 57426 | 8388608 | confirmado |

Sessão `20261023T043912Z_38579`. Domínio `RDRAM` acessível diretamente via `memory.getmemorydomainsize("RDRAM")` com tamanho 8 MiB, embora não listado em `memory.getmemorydomainlist()`; a divergência com os `0x200000` endereços indicados no Hex Editor permanece sem resolução. O arquivo A1 tem SHA-256 `E69552A8579195ADFE99579CC50CB99AF31983795A54AD1F87CD38730BC09E57` (hash fornecido pelo operador); hashes de B e A2 não foram coletados.

Resultado de `python .\\tools\\analyze_autoaim_mem_v1.py`: **323702 bytes diferentes** na comparação A1/B e **23287 offsets reversíveis** `A1==A2!=B` (7,19% dos bytes alterados). Arquivo local de saída: `output/csv/autoaim_mem_v1_candidates_20261023T043912Z_38579.csv`; dumps locais: `output/archive/autoaim_mem_v1_20261023T043912Z_38579_{A1,B,A2}.bin`.

Exemplos (offsets na memória-domínio, **não** endereços de RAM validados): `0x0232C3 0/1/0`, `0x040A93 1/0/1`, `0x04838B 1/0/1`, `0x05D6DF 0/1/0`, `0x05D6E7 8/0/8`. Esses registros continuam como `candidate_reversible_byte_only`, não demonstram que representem a configuração do auto-aim.

O inventário canônico do experimento (sem dumps completos, sem promover símbolos) está em [GoldenEye.mapping — experiments/autoaim_memory_discovery_v1_20261023.json](https://github.com/marcosvilhena87/GoldenEye.mapping/blob/main/experiments/autoaim_memory_discovery_v1_20261023.json).

**Pendências:** verificar hash da ROM carregada, núcleo N64, amostras repetidas entre sessões independentes, estado do menu sem alteração de opção, estabilidade temporal e sem alvo. Não adicionar nenhum dos 23287 offsets ao `catalog/symbols.json` como `validated` com base nesta sessão. Guardar CSV e dumps no computador do operador; não subir arquivos binários nem ROM ao GitHub. Um erro transitório `WinError 5` no envio de A2 por substituição do arquivo de requisição foi superado em nova tentativa; recomendada fila de comandos por arquivo na próxima versão.

