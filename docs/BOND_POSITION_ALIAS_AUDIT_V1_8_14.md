# Bond Position Validation v1.8.14 — Spatial Return & Alias Divergence Audit

Audit **offline** de uma sessão v1.8.13 já capturada. Não precisa carregar outro Lua nem repetir o experimento.

## Objetivos
- Localizar os frames em que pares `0x06D248/0x0D33EC` e `0x06D250/0x0D33F4` divergem byte a byte.
- Inspecionar fase, valores RAW, interpretação float32 BE e coincidência com valores do frame anterior ou seguinte.
- Comparar igualdade com deslocamentos de 1 e 2 frames apenas como diagnósticos de possível atraso, **não como prova de latência**.
- Calcular vetores candidatos de ida/volta, cosseno entre direções, soma e erro de fechamento; não substituir validação física independente.

## Executar
```powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_position_v1_8_14 -v
$sid = "20261025T181441Z_9591"
python -m tools.audit_bond_position_v1_8_14 $sid
$r = Get-Content ".\output\csv\bond_position_v1_8_14_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.aliases | Select-Object left,right,frames_compared,divergence_count,equal_fraction,divergences_by_phase | Format-List
$r.divergence_frames | Format-Table -AutoSize
$r.routes.primary | Format-List
```

O arquivo de saída não é sobrescrito automaticamente.

## Restrições
A identificação do Soldier #1, os eixos X/Z de Bond, a execução física exata de movimentos reversos e o retorno visual à origem não estão comprovados apenas pela RDRAM. Igualdade bruta imperfeita não significa necessariamente atraso: pode decorrer de ordem de atualização, valores derivados ou eventos do jogo. Testar em outra sessão/save é necessário antes da promoção ao `GoldenEye.mapping`.
