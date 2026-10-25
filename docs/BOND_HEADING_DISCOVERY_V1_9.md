# Bond Heading Discovery v1.9 — Rotation-responsive Memory Discovery

## Objetivo
Avaliar os candidatos de rotação `0x0D3998` / `0x0D3D40` (833 pares de eventos sincronizados em v1.5.1) e seus vizinhos, `0x0D36F4` / `0x0D3720` (u8 não validados) contra os controles de posição `0x0D33EC`, `0x0D33F4`, `0x06D248`, `0x06D250`.

A coleta é RDRAM 8MiB **somente leitura**. Sem uso automático de joystick, cheats ou disparos.

## Instalação
```powershell
git pull --ff-only origin main
python -m unittest tests.test_bond_heading_v1_9 -v
New-Item -ItemType Directory -Force output\csv,output\commands,output\sessions | Out-Null
```
Inicie `bond_heading_discovery_v1_9.lua` pela Lua Console do BizHawk, com diretório de trabalho na raiz do repositório.

## Fases
Envie cada marcador com `python -m tools.send_bond_heading_v1_9 LABEL`, aguarde `MARKED` e permaneça idealmente 120+ frames em cada fase:

1. BASELINE_STILL: Bond imóvel sem alvo, auto-aim OFF.
2. TURN_LEFT: girar Bond à esquerda, sem caminhar.
3. STILL_LEFT: parar.
4. TURN_RIGHT: girar Bond à direita, sem caminhar.
5. STILL_RETURN: parar com direção aproximadamente original.
6. TURN_FULL_CIRCLE: completar giro de 360° estimado visualmente; observar wrap-around, não presumir escala.
7. STILL_FULL_CIRCLE: parar.
8. MOVE_FORWARD: translação sem girar.
9. STILL_AFTER_MOVE: parar.
10. MOVE_BACK: voltar mantendo orientação.
11. STILL_FINAL: parar.
12. AIM_ON_NO_TARGET_TURN: ativar auto-aim ON manualmente e girar sem alvo visível.
13. AIM_OFF_NO_TARGET_TURN: voltar a OFF manualmente e repetir giro.
14. STOP.

Ao alternar auto-aim, permita frames suficientes e confirme a opção manualmente antes de marcar a fase.

## Executar análise
```powershell
$sid=(Get-Content ".\output\sessions\bond_heading_v1_9_session.txt" -Raw).Trim()
python -m tools.analyze_bond_heading_v1_9 $sid
$r=Get-Content ".\output\csv\bond_heading_v1_9_${sid}_analysis.json" -Raw | ConvertFrom-Json
$r.complete
$r.candidates | Select-Object -First 20 offset,tracked,turn_change_rate,still_change_rate,move_change_rate,rotation_specificity_score | Format-Table -AutoSize
$r.candidates | Where-Object { $_.offset -in @("0X0D3998","0X0D3D40") } | Format-List
```

## Limitações
A classificação ordena taxas de alterações RAW durante giro versus movimento e imobilidade, sem inferir graus/radianos, monotonicidade, periodicidade, sentido correto ou yaw confirmado. O formato de gravação é de quatro bytes, incluindo controles unaligned; para entradas u8 deve-se examinar o byte correto. Uma rotação manual pode ter deslocamento residual. Validação de heading requer referencial angular externo, wrap-around e replicação entre sessões. Nenhum símbolo é promovido automaticamente ao GoldenEye.mapping.
