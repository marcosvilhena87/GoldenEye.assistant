# Soldier Coordinate Discovery v1.8.13 — Bond Position Candidate Validation

A v1.8.12 indicou variação forte dos candidatos de Bond sob translação e pequena sob rotação. A v1.8.13 verifica retorno numérico à origem, repetição de destino, controles de giro e constância de campos candidatos do Soldier #1 congelado.

## Preparação
```powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_position_v1_8_13 -v
New-Item -ItemType Directory -Force output\csv,output\commands,output\sessions | Out-Null
```
Carregue `bond_position_validation_v1_8_13.lua` no BizHawk na raiz do repositório. Não utiliza escrita de memória. Exige RDRAM de 8 MiB. Garanta que o soldado permaneça congelado e não altere a opção de auto-aim durante a sessão.

## Etapas
Envie uma por vez com `python -m tools.send_bond_position_v1_8_13 LABEL` e aguarde `MARKED`. Observar idealmente ao menos 120 frames por fase.

1. BASELINE — Bond e Soldier #1 visíveis/parados.
2. FREEZE_REQUEST_ON — ativar Freeze manualmente.
3. FREEZE_CONFIRMED — confirmar soldado imóvel.
4. ORIGIN_STILL — Bond parado em um ponto visual de referência.
5. ROTATE_LEFT — girar sem caminhar.
6. ROTATE_RIGHT — girar para voltar à orientação original, sem caminhar.
7. ORIGIN_AFTER_ROTATION — Bond parado após rotação.
8. MOVE_FORWARD — caminhar em linha aproximadamente reta.
9. DESTINATION_STILL — parar e registrar visualmente o destino.
10. MOVE_BACK — recuar em linha reta ao mesmo ponto físico inicial.
11. RETURN_STILL — confirmar retorno visual ao ponto inicial.
12. MOVE_FORWARD_REPEAT — repetir percurso aproximado.
13. DESTINATION_REPEAT_STILL — confirmar destino visual similar.
14. MOVE_BACK_REPEAT — recuar ao ponto original.
15. RETURN_REPEAT_STILL — confirmar retorno visual.
16. STOP — terminar.

Os marcadores não controlam Bond nem ativam Freeze. O posicionamento e a orientação reais são observações externas, não medidos por esse protocolo.

## Análise
```powershell
$sid=(Get-Content ".\output\sessions\bond_position_v1_8_13_session.txt" -Raw).Trim()
python -m tools.analyze_bond_position_v1_8_13 $sid
$r=Get-Content ".\output\csv\bond_position_v1_8_13_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.capture_complete
$r.phase_frame_counts
$r.results | Select-Object bond_pair,return_error_by_phase,repeat_destination_error,max_still_numeric_spread | Format-List
$r.aliases | Format-Table -AutoSize
```

O relatório distingue erros numéricos de retorno à origem `RETURN_STILL` e `RETURN_REPEAT_STILL`, desvio após rotação `ORIGIN_AFTER_ROTATION`, erro do destino repetido, intensidade das fases e constância dos candidatos do soldado. Não aplica um limite físico arbitrário e não valida eixos X/Z automaticamente.

## Comparação entre sessões
Execute duas capturas independentes, de preferência em novos saves com contexto explicitamente registrado. Depois compare os arquivos de análise:
```powershell
python -m tools.compare_bond_position_v1_8_13 .\output\csv\bond_position_v1_8_13_SESSAO_A_analysis.json .\output\csv\bond_position_v1_8_13_SESSAO_B_analysis.json
```
Sem identificação independente de save/ROM, duas sessões distintas não são comprovação de persistência entre saves. Nenhuma promoção automática ao GoldenEye.mapping.
