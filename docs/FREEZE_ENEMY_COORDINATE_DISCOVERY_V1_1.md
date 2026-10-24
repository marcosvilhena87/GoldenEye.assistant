# Freeze Enemy Coordinate Discovery v1.1 — alternância reversível
Observação do operador (24/10/2026): Freeze OFF permite movimento; Freeze ON paralisa inimigo onde está; ao desligar, o inimigo volta a caminhar **do mesmo ponto**. No Cheat Search foi observado `02C90C d u 0 RDRAM`; o usuário relata `0 = desligado` e `diferente de 0 = ligado`. Evidência relatada, **ainda sem dumps/ROM SHA/core verificados**. Esse byte **não é XYZ**, nem a escrita pelo GameShark prova causalidade direta.

## Hipótese operacional
Encontrar campos espaciais específicos da instância do inimigo que mudam entre P1→P2→P3 (Freeze OFF), mantendo-se estáveis em cada ON/HOLD, inclusive durante rotação de Bond. Separar posições do mundo de câmera, IA, animação e velocidade. Comparar múltiplos inimigos, e testar também um OFF sem cheat desde o início (controle negativo).

## Preparação
Criar `output/raw`, `output/commands`, `output/sessions`; iniciar jogo no BizHawk. Verificar manualmente que o Cheat Search exibe `02C90C` como byte unsigned no domínio **RDRAM** e que de fato acompanha a mudança ON/OFF. O script interrompe se o tamanho do domínio RDRAM não for 8 MiB. Não injeta cheat, botões, savestates ou escrita de memória.

Executar `freeze_enemy_capture_v1_1.lua` pelo console Lua. Ler o session id informado no console, ou o arquivo `output/sessions/freeze_enemy_v1_1_<id>_pointer.txt`. Capturar por comandos `output/commands/freeze_enemy_v1_1_<id>_<N>.txt` cujo conteúdo seja exatamente o rótulo da fase (sem distinção de espaços finais). **Somente avançar após `captured`.** Se o flag lido não bater, a sessão aborta para não fabricar identificação de estado; reinicie em outra sessão.

## Ordem
| Índice | Marker | Freeze | Ação |
|---|---|---|---|
| 1 | p1_on | ON | Parar inimigo em P1 |
| 2 | p1_hold | ON | Bond e inimigo imóveis |
| 3 | move1_off | OFF | Deixar inimigo caminhar; captura durante movimento |
| 4 | p2_on | ON | Parar em P2 |
| 5 | p2_hold | ON | Confirmar estabilidade |
| 6 | move2_off | OFF | Segundo deslocamento |
| 7 | p3_on | ON | Parar em P3 |
| 8 | p3_hold | ON | Confirmar estabilidade |
| 9 | rotate_on | ON | Girar Bond parado e capturar |

Exemplo PowerShell após identificar `$sid`:
```powershell
Set-Content ".\output\commands\freeze_enemy_v1_1_${sid}_1.txt" "p1_on"
```
Repetir para os demais índices/fases. O manifesto registra frames e o valor lido do flag. Não confundir `move1_off`/ `move2_off` com marcos estáveis: são controles de transição.

## Investigação posterior
Os nove snapshots são de 8 MiB, gerados com leitura read-only de byte. Cada arquivo representa o domínio RDRAM, não uma captura de tela. O dump bloqueia a execução Lua; comparar `frame` e `frame_after` para detectar mudança durante a leitura. Usar bytes crus; testar offsets alinhados, ambos endianismos e tipos plausíveis sem presumir f32. Priorizar padrões P1 estável / P2 diferente / P2 estável / P3 diferente / P3 estável, invariância em rotação. Confirmar instância e coordenadas por dois eixos físicos e entre sessões. Não registrar como `validated` no `GoldenEye.mapping` sem prova.

**Ressalva:** a revisão v1.1 é um coletor novo; `tools/analyze_freeze_enemy_v1.py` espera a sequência anterior de cinco dumps, portanto **não deve** ser aplicado diretamente aos nove arquivos. Novo analisador comparativo é etapa subsequente.
