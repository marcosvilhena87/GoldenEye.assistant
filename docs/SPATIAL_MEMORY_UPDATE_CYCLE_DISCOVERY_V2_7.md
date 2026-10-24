# Spatial Memory Update Cycle Discovery v2.7

Auditoria offline da captura bruta v2.4, usando 12 bytes pertencentes aos blocos experimentais `0x3B30D0`, `0x3B30E0` e `0x3B30EC`. Não acessa o emulador, não escreve na memória e não altera `GoldenEye.mapping`.

## Execução no PowerShell
```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_cycle_v2_7 -v
$session = '20261024T152944Z_311185'
python .\tools\analyze_spatial_cycle_v2_7.py $session
```

Relatórios criados, sem sobrescrita:
- `spatial_v2_7_<session>_leadlag.csv`: 7 lags −3 a +3 para os 12 pares de bytes homólogos entre blocos. Outros pares são avaliados somente em lag zero. Lag positivo significa mudança à direita ocorrendo depois da mudança à esquerda.
- `spatial_v2_7_<session>_cycle_lags.csv`: correspondência de valores em lags 6, 13 e 19, comparada aos lags vizinhos para cada byte e fase.
- `spatial_v2_7_<session>_cochange_groups.csv`: pares de bytes com coeficiente phi e grupos candidatos com phi ≥ 0,7 em lag zero. Grupos são apenas pares, não estruturas comprovadas.

## Consultas
```powershell
Import-Csv ".\output\csv\spatial_v2_7_${session}_leadlag.csv" |
 Where-Object { $_.phase -eq 'P0_HOLD' -and $_.left -eq '0x3B30D0' -and $_.right -eq '0x3B30E0' } |
 Select-Object lag,phi,null_phi_mean,null_phi_max,empirical_one_sided_p | Format-Table -AutoSize

Import-Csv ".\output\csv\spatial_v2_7_${session}_cycle_lags.csv" |
 Where-Object { $_.address -in @('0x3B30D0','0x3B30E0') } |
 Select-Object phase,address,lag,raw_match_rate,local_excess | Format-Table -AutoSize
```

## Significado estatístico e limitações

O controle de sincronização desloca circularmente uma das séries binárias (alterou/não alterou), mantendo sua composição e estrutura temporal interna. Exclui deslocamentos próximos de zero, usa até 199 deslocamentos determinísticos, e relata uma fração empírica unilateral; não é significância confirmatória após múltiplos testes e não permite inferir causalidade.

A detecção de ciclo é descritiva, comparando diretamente um lag às duas defasagens vizinhas. Não se aplica deslocamento circular à própria série para testar periodicidade, pois isso preservaria a estrutura de recorrência e seria um controle inadequado. A comparação entre fases diferentes ainda depende da duração e da qualidade dos marcadores manuais.

Todos os resultados são observações experimentais; nenhuma coordenada, ponteiro ou layout é validado automaticamente.
