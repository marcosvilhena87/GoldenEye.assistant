# Soldier Coordinate Discovery v1.8.7 — Entity Spatial Identity & Freeze Timing
Experimento somente leitura; nenhum eixo XYZ ou identidade de entidade validada.
Execute soldier_entity_identity_v1_8_7.lua na Lua Console do BizHawk, partindo da raiz do repositorio.
Crie output/csv, output/commands, output/sessions. RDRAM deve ter exatamente 8 MiB.
Envie marcadores individualmente com python -m tools.send_soldier_identity_v1_8_7 LABEL, aguardando MARKED e observando cerca de 120 frames por fase.
Ordem: BASELINE, IDENTITY_VISUAL_CONFIRMED, BOND_ROTATE, BOND_MOVE, SOLDIER_MOVING, FREEZE_REQUEST_ON, FREEZE_CONFIRMED, FREEZE_REQUEST_OFF, SOLDIER_RESTARTED, STOP.
FREEZE_CONFIRMED apenas registra a observacao visual do operador, nao prova o freeze por RAM.
Analise:
```powershell
$sid = (Get-Content ".\output\sessions\soldier_identity_v1_8_7_session.txt" -Raw).Trim()
python -m tools.analyze_soldier_identity_v1_8_7 $sid
$r = Get-Content ".\output\csv\soldier_identity_v1_8_7_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.freeze_episodes | Format-List *
$r.duplicate_pairs | Format-Table -AutoSize
```
quiet_window_observed mede a primeira janela disponivel retrospectiva sem alteracoes; nao estabelece instante causal de congelamento.
Para comparar outro save reinicie a Lua, preserve cada SID e repita fases. Nao carregar savestates durante a captura.
Nao promover offsets para GoldenEye.mapping sem verificacao independente de coordenadas, identidade e ROM/core.
