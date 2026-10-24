# Freeze Address Mapping v1.1 — Transition Synchronization

## Baseline experimental
No experimento v1, KSEG0 e KSEG1 variaram juntos em `698198: 0→255`, `700108: 255→0` e `702077: 0→255`. Os marcadores manuais foram registrados em frames diferentes (696092 OFF1, 698573 ON1, 699545 OFF2, 701383 ON2, 703442 STOP). Esses intervalos não provam latência do cheat. A leitura física direta `0x0002C90C` permaneceu 255. O RAM Watch mostrava offset `0x02C90C`, domínio rotulado RDRAM, OFF=0 e ON=255 conforme operador.

## Execução
No diretório `GoldenEye.assistant`:
```powershell
git pull --ff-only origin main
New-Item -ItemType Directory -Force .\output\csv,.\output\commands,.\output\sessions
python -m unittest tests.test_freeze_address_v1_1 -v
```
Abra GoldenEye no BizHawk e carregue `freeze_address_mapping_v1_1.lua` em Tools > Lua Console. Verifique o RAM Watch durante todo o experimento. Alterne o Freeze manualmente OFF→ON→OFF→ON, deixando cada estado estável por pelo menos 60 frames. Não use marcadores OFF/ON. O script lê apenas o System Bus; a janela Lua pode não disponibilizar RDRAM. Não escreve na RAM, não injeta controles e não altera cheats.

Quando terminar:
```powershell
python .\tools\send_freeze_address_v1_1.py STOP
$sid=(Get-Content .\output\sessions\freeze_address_v1_1_session.txt).Trim()
python .\tools\analyze_freeze_address_v1_1.py $sid
```
Espere `finished reason=stop` no console.

## Dados
`output/csv/freeze_address_v1_1_<sid>_timeline.csv` contém leituras por frame dos 3 endereços.
`_events.csv` contém `BASELINE_CONFIRMED`, `TRANSITION_CONFIRMED`, `ALIAS_UNCERTAIN`, `STATE_RECONFIRMED`, `DISCONTINUITY`.
`_termination.csv` contém razão final, quantidade de erros e divergências.
`_analysis.json` resume concordância e transições.

Um evento confirmado em `frame` significa que 30 amostras consecutivas já comprovaram aquele novo estado; o campo `run_start_frame` marca a primeira leitura do trecho estável. Portanto, a confirmação vem tipicamente 29 frames após a primeira observação, não mede latência de jogo. `ALIAS_UNCERTAIN` significa leitura inválida, valores diferentes ou valores fora de 0/255. Não considerar o estado confirmado durante trechos incertos; o CSV mantém a evidência para revisão.

## Limitações / critérios
Um dos dois aliases mudar junto com o cheat não é prova suficiente: exigir identidade ROM/núcleo, controles com RAM Watch, comparação após restart/savestate, repetição em outra sessão e ausência de ambiguidade. Somente após resolver o endereçamento incorporar um leitor de estado aos capturadores espaciais. Nenhum desses endereços é uma coordenada XYZ. O arquivo `GoldenEye.mapping` mantém status preliminar e não deve promover símbolo canônico nesta etapa.
