# GoldenEye Auto-Aim Mapping v2 — Operador e controles negativos

**Meta:** mapear condições de acionamento da mira assistida original, sem confundir assistência automática, mira manual (R) e disparo (Z). Não há endereço de memória de auto-aim confirmado.

## Fonte de dados e limites

- `output/csv/autoaim_v2_events.csv`: fases, eventos marcados manualmente, notas e eventuais mudanças brutas dos rótulos R/Z do BizHawk. Rótulos brutos são auxiliares e não comprovam ações realizadas no jogo.
- `output/csv/autoaim_v2_samples.csv`: heartbeat a cada 30 frames marcado `operator_only`; não contém posição do alvo nem ângulo de mira.
- `output/csv/autoaim_v2_diagnostics.csv`: inicialização e erros de comando.
- `output/sessions/autoaim_v2_session.txt`: sessão vinculada à fila.
- `GoldenEye.mapping/catalog/symbols.json` permanece sem símbolos inventados.

## Preparar

1. Encerre outros scripts observadores na Lua Console; retorne ao repositório raiz como diretório de trabalho.
2. Execute `python .\tools\prepare_output.py`; abra `autoaim_mapping_v2.lua` no BizHawk.
3. Escolha uma arma, uma distância, uma posição do jogador e um inimigo isolado. Repita o cenário por savestate se possível. Registre núcleo N64 e versão da ROM se disponíveis.
4. Antes de cada condição, em PowerShell: `python .\tools\send_autoaim_v2.py PHASE no_target_enabled` (por exemplo). Use `EVENT` para resultados observados, sem declarar um acerto se ele não ocorreu.

## Plano de contrastes

| Fase | Condição | O que registrar |
|---|---|---|
| no_target_enabled | auto-aim ativado, nenhum alvo visível | alteração visual da mira e ausência/presença de tiro |
| target_enabled | auto-aim ativado, inimigo isolado visível | câmera/mira, alvo, disparo, acerto observável |
| target_disabled | auto-aim desativado, cena equivalente | diferenças em relação à anterior |
| manual_aim_r | R pressionado para mirar | distinguir mira manual da assistida |
| target_occluded | inimigo encoberto | presença/ausência de auxílio |
| target_offset | inimigo deslocado do centro | condições de engajamento |

Exemplos, um de cada vez após a ação no jogo:

```powershell
python .\tools\send_autoaim_v2.py PHASE no_target_enabled
python .\tools\send_autoaim_v2.py EVENT no_adjustment_observed
python .\tools\send_autoaim_v2.py PHASE target_enabled
python .\tools\send_autoaim_v2.py EVENT aim_shift_observed
python .\tools\send_autoaim_v2.py NOTE same_weapon_same_position
```

**Não envie as fases em lote:** realize e observe cada condição antes da fase seguinte. Comparar tiros feitos de condições semelhantes, incluindo negativo sem alvo e assistente desligado. O script não controla o jogo, nem faz auto-shot, nem comprova o auto-aim sem a observação do operador.

## Critérios de avanço

1. Estabelecer diferenças reproduzíveis em cenários controlados e registrar frames.
2. Procurar, em experimento separado, candidatos de memória usando diferenças com/sem auto-aim. Endereços encontrados são `candidate`, nunca automaticamente `validated`.
3. Promover ao mapping somente evidência comprovada, com versão da ROM, núcleo e proveniência.
