# Spatial Position Discovery v2.2 — Periodicity & Memory Structure Validation

Dois módulos independentes: (1) análise estatística **offline** de dados v1.9 já capturados e (2) sondagem **opcional, nova**, somente de leitura, de janela de 80 bytes em RDRAM. Nenhum endereço é validado ou copiado para o catálogo canônico automaticamente.

## Etapa A — Sem nova captura

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_position_discovery_v2_2 -v
$session='20261024T143653Z_122842'
python .\tools\analyze_spatial_position_v2_2.py $session
Import-Csv ".\output\csv\spatial_v2_2_${session}_periodicity.csv" |
 Where-Object { $_.phase -eq 'BASELINE_HOLD' } |
 Sort-Object { -[double]$_.excess_match } |
 Select-Object -First 20 phase,address,lag,raw_match_rate,iid_expected_match,excess_match,permutation_p |
 Format-Table -AutoSize
```

O teste de permutação embaralha os dados preservando a frequência dos valores, com **199 repetições** e semente fixa. Para controlar custo, cada fase é avaliada usando seus **primeiros 512 frames**; estatísticas observadas e nulas utilizam os mesmos frames. Os valores de p são **exploratórios e não corrigidos para múltiplas comparações**, não confirmam ciclos. Usar `--max-lag 64`, `--permutations 99` ou `--seed 123` é opcional; cada execução produz um arquivo exclusivo e se recusa a sobrescrever o anterior. Os picos de 6, 13 e 19 frames serão testados contra coincidências esperadas pela frequência dos estados.

## Etapa B — Janela adjacente opcional (nova sessão)

Script Lua `spatial_position_discovery_v2_2.lua`: intervalo fixo **0x3B30B0–0x3B30FF**, cobrindo ambos candidatos, 80 bytes por frame até STOP ou 18.000 frames. Caminho separado de saída, sem memória presumida além da **janela explicitamente experimental**. Antes de iniciar, verifique o domínio e configure:

```lua
local DOMAIN="RDRAM"
local EXPECTED_SIZE=8388608
```

Garanta diretórios `output/csv`, `output/commands`, `output/sessions` já existentes (`python .\tools\prepare_output.py`). No BizHawk inicie o novo Lua, sem savestates durante a sessão.

Marque **antes** de cada intervenção, aguarde `[spatial.v2.2] marked <LABEL>` e só então altere os controles. Sequência: `STILL` (sem mover), `MOVE` (avançar), `HOLD` (imóvel), `ROTATE` (somente girar), `ROTATE_HOLD` (imóvel), `STOP`. Deixe cada fase durar alguns segundos.

```powershell
python .\tools\send_spatial_v2_2.py STILL
# depois do marcador, manter parado; repetir, um de cada vez:
python .\tools\send_spatial_v2_2.py MOVE
python .\tools\send_spatial_v2_2.py HOLD
python .\tools\send_spatial_v2_2.py ROTATE
python .\tools\send_spatial_v2_2.py ROTATE_HOLD
python .\tools\send_spatial_v2_2.py STOP
```

Após `FINISHED ... reason=stop`:

```powershell
$session=(Get-Content .\output\sessions\spatial_v2_2_session.txt -Raw).Trim()
python .\tools\analyze_spatial_window_v2_2.py $session
Import-Csv ".\output\csv\spatial_v2_2_${session}_window_summary.csv" |
 Sort-Object phase,offset | Format-Table -AutoSize
```

A auditoria da janela resume mudança por endereço e fase. **Ela não descobre automaticamente ponteiros, limites de estruturas nem propriedade de Bond**, que exigiriam evidência externa e validação adicional. Preserve os CSVs originais e não comite dumps de memória.
