# Spatial Position Discovery v2.3 — Memory Field Reconstruction & Cross-Phase Validation

A v2.3 reutiliza a captura da janela v2.2, **sem novas capturas nem modificação da memória do GoldenEye**. Reconstrói campos **alinhados em relação à janela RDRAM** de 16 e 32 bits para todos os 80 bytes de `0x3B30B0` a `0x3B30FF`. Cada interpretação é experimental, nunca validada automaticamente.

## Executar

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_position_discovery_v2_3 -v
$session='20261024T151540Z_261121'
python .\tools\analyze_spatial_position_v2_3.py $session
```

Arquivos gerados em `output/csv`, sem sobrescrever dados existentes:

- `spatial_v2_3_<session>_fields.csv` — para cada endereço alinhado, interpretações `u16`, `i16`, `u32`, `i32`, `f32` em big/little endian. Inclui taxa de mudanças, amplitude, deslocamento líquido, proporção de valores finitos e diferenças entre MOVE/STILL/HOLD/ROTATE/ROTATE_HOLD.
- `spatial_v2_3_<session>_boundaries.csv` — comparação de janelas de até 30 frames antes/depois de cada marcador, com medianas, salto e valores extremos próximos à transição.

Total esperado, com dados íntegros: **280 interpretações** e **1.120 registros de fronteira**.

```powershell
Import-Csv ".\output\csv\spatial_v2_3_${session}_fields.csv" |
 Sort-Object { -[double]$_.movement_contrast } |
 Select-Object -First 20 offset,width,interpretation,still_change_rate,move_change_rate,hold_change_rate,movement_contrast,evidence_for,evidence_against |
 Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_3_${session}_fields.csv" |
 Where-Object { $_.interpretation -eq 'be_f32' } |
 Select-Object offset,move_range,still_range,hold_range,finite_fraction,evidence_against |
 Format-Table -AutoSize
```

**Interpretação:** uma taxa de mudanças maior em MOVE do que em STILL/HOLD é apenas uma observação, não uma prova de coordenada; a magnitude e a direção precisam ser verificadas em experimentos posteriores controlados. Variações elevadas durante fases de HOLD representam evidência contrária à hipótese de coordenada estável, mas não necessariamente a descartam se as fases foram marcadas imprecisamente. A comparação das fronteiras é descritiva, não causal.

As análises abrangem apenas campos alinhados de 2 e 4 bytes. Não descobrem ponteiros de jogador, estruturas fora da janela, nem reconhecem XYZ. Os marcadores STOP e a integridade dos dados são obrigatórios.
