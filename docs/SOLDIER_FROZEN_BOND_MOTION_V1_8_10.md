# Soldier Coordinate Discovery v1.8.10 — Frozen Soldier, Bond-Only Motion

Somente leitura de RDRAM. Objetivo: verificar se a distancia candidata de dois componentes converge durante o movimento de Bond **enquanto os campos candidatos do soldado ficam invariantes**. A identidade real de Soldier #1 e os eixos X/Z continuam hipoteticos.

## Executar
Na raiz de GoldenEye.assistant: `git pull --ff-only origin main`; `python -m unittest tests.test_soldier_frozen_v1_8_10 -v`. Crie `output/csv`, `output/commands`, `output/sessions`, carregue `soldier_frozen_bond_motion_v1_8_10.lua` no BizHawk. RDRAM precisa ter 8 MiB.

Envie um marcador por vez com `python -m tools.send_soldier_frozen_v1_8_10 LABEL`; aguarde `MARKED` antes do seguinte. Mantenha aproximadamente 120 frames por fase e efetue os movimentos no jogo:

1. `BASELINE`: Bond e soldado observados em repouso.
2. `FREEZE_REQUEST_ON`: ative o cheat Freeze.
3. `FREEZE_CONFIRMED`: confirme visualmente que o Soldier #1 parou; mantenha Freeze ligado ate STOP.
4. `FROZEN_BASELINE`: Bond parado, soldado congelado.
5. `BOND_APPROACH`: aproxime Bond do soldado congelado.
6. `BOND_STOP_NEAR`: Bond parado proximo do soldado.
7. `BOND_ROTATE`: gire somente a visao de Bond, sem translacao.
8. `BOND_RETREAT`: afaste Bond do soldado.
9. `BOND_STOP_FAR`: Bond parado longe do soldado.
10. `STOP`: encerre a captura.

## Analisar
```powershell
$sid=(Get-Content ".\output\sessions\soldier_frozen_v1_8_10_session.txt" -Raw).Trim()
python -m tools.analyze_soldier_frozen_v1_8_10 $sid
$r=Get-Content ".\output\csv\soldier_frozen_v1_8_10_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.results | Select-Object config,frozen_fields_constant_across_stages,approach_converged,retreat_diverged,rotation_distance_stable,controlled_convergence_supported | Format-Table -AutoSize
```

O analisador exige ausencia de mudancas nos dois campos candidatos do soldado atraves das fases pos-Freeze para aceitar convergencia controlada. A estabilidade na rotacao usa limiar 0.01 em unidades numericas hipoteticas, NAO distancia fisica provada. A leitura de diferentes enderecos ocorre sequencialmente por frame. Repetir em save novo e nao promover simbolos automaticamente ao GoldenEye.mapping.
