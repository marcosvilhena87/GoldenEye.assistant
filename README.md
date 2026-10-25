# GoldenEye.assistant

Assistente experimental para **GoldenEye 007 (Nintendo 64)**, com inicialização centralizada em `main.lua`.

## Segurança de integração
- `GoldenEye.mapping` é a fonte canônica: https://github.com/marcosvilhena87/GoldenEye.mapping
- Nenhum endereço, ponteiro, offset ou comportamento de RAM é presumido neste projeto.
- Modo normal: apenas símbolos `validated`, da ROM correta, com domínio, largura, endianidade e contexto compatíveis.
- Ausência ou ambiguidade de dados: **falhar fechado**, sem leitura/escrita e sem comandos.
- O snapshot do catálogo não é incluído no repositório; exporte-o de um checkout auditado do mapping.
- Nenhuma automação de disparo está habilitada nesta versão.

## Arquitetura
```text
main.lua
lua/{memory,player,enemies,auto_aim,auto_shot,controller}.lua
config/assistant.lua
tools/export_mapping.py
tests/test_export_mapping.py
docs/ARCHITECTURE.md
```

## Preparação
1. Identifique a versão da ROM e o núcleo/versão do emulador.
2. Faça checkout de `GoldenEye.mapping` e confira o commit desejado.
3. Execute `python tools/export_mapping.py CAMINHO_DO_MAPPING --rom-id IDENTIFICADOR --output config/mapping_snapshot.lua`.
4. Execute `python -m unittest discover -s tests -v`.
5. Carregue `main.lua` no ambiente Lua compatível (adaptador de emulador ainda não configurado).

**Estado inicial:** todos os catálogos de memória continuam vazios; exportar um snapshot vazio não habilita leituras.

Não distribuir ROMs ou dumps proprietários.

## Arquivos gerados
Os observadores ativos de controles v2.2.1 e analógico v1 gravam em `output/csv/`, `output/sessions/` e `output/commands/`. Execute `python tools/prepare_output.py --migrate` (com a Lua Console parada) após atualizar o repositório. Veja [docs/OUTPUT_LAYOUT.md](docs/OUTPUT_LAYOUT.md). Arquivos-fonte Lua ficam em `lua/`, e os inicializadores continuam na raiz para compatibilidade.

## Auto-Aim Memory Discovery v1 — evidências coletadas

O procedimento de captura A/B/A na RDRAM (8 MiB por snapshot) foi executado na sessão `20261023T043912Z_38579`: 323.702 diferenças A1/B e 23.287 offsets reversíveis `A1=A2!=B`. Esses valores são **candidatos experimentais**, não símbolos de memória validados. Veja [o relatório e protocolo](docs/AUTOAIM_MEMORY_DISCOVERY_V1.md) e [o registro canônico de evidências no GoldenEye.mapping](https://github.com/marcosvilhena87/GoldenEye.mapping/blob/main/experiments/autoaim_memory_discovery_v1_20261023.json).

Os binários e o CSV integral permanecem locais em `output/`; não publicar ROM, dumps ou snapshots do jogo. A identidade hash da ROM usada ainda não foi confirmada. Nenhum endereço foi incluído no catálogo de símbolos.

## Auto-Aim Memory Discovery v1.1

Implementado coletor experimental [v1.1](docs/AUTOAIM_MEMORY_DISCOVERY_V1_1.md) com seis snapshots controlados (`A1, A_STABLE, B, B_STABLE, A2, CONTROL_A`), requisições numeradas sem substituição concorrente, gravação de dumps em blocos e analisador que filtra instabilidade e menu sem mudança de opção. Inclui teste sintético de regressão. Execute `python -m unittest discover -s tests -v` e confira as instruções para configuração manual de domínio e tamanho antes de abrir `autoaim_memory_discovery_v1_1.lua` no BizHawk. **Nenhum novo offset foi validado;** os 23.287 candidatos da v1 são somente evidência a filtrar.

## Auto-Aim Memory Discovery v1.2 — Candidate Validation

[Protocolo e comandos da v1.2](docs/AUTOAIM_MEMORY_DISCOVERY_V1_2.md): gerador de watchlist local a partir dos 131 candidatos comuns da v1/v1.1 (não presumidos), coletor Lua de leituras direcionadas, oito estados de teste com controles e analisador CSV de estabilidade. O processo é **somente leitura da RDRAM**; os símbolos canônicos não são promovidos antes de identidade ROM/núcleo confirmada, reinício e testes negativos. Código publicado, execução real no BizHawk ainda pendente.

## Auto-Align de Bond (planejamento)

O [Auto-Align Roadmap v1](docs/AUTOALIGN_ROADMAP_V1.md) define a evolução da leitura validada do Auto-Aim horizontal para um controlador limitado de giro de Bond, com calibração, zona morta, interrupção segura e testes sem disparo. Depende das descobertas canônicas no [GoldenEye.mapping](https://github.com/marcosvilhena87/GoldenEye.mapping/blob/main/docs/AUTOAIM_HORIZONTAL_AUTOALIGN_V1.md). **Ainda não há Auto-Align funcional nem Auto-Shot habilitado.**

## Auto-Aim Memory Discovery v1.4 — Temporal Monitoring

[Protocolo v1.4](docs/AUTOAIM_MEMORY_DISCOVERY_V1_4.md): observador somente leitura dos cinco offsets experimentais por frame, com registro de transições e marcadores do operador. A análise temporal gera um resumo independente para cada sessão, preservando todos os CSVs das versões anteriores. **Os offsets não são símbolos validados e não há automação da mira ou disparo.**

## Auto-Aim Memory Discovery v1.4.1 — Temporal Event Correlation

[Analisador offline v1.4.1](docs/AUTOAIM_MEMORY_DISCOVERY_V1_4_1.md): agrupa transições em episódios, correlaciona com marcadores de operador (janela configurável), verifica sincronização entre `0x0D308B` e `0x0D309B` e identifica rampas monotônicas. Opera somente nos CSVs existentes, sem modificar evidências históricas ou validar símbolos automaticamente.

## Auto-Aim Memory Discovery v1.5 — Semantic Field Identification

[Protocolo v1.5](docs/AUTOAIM_MEMORY_DISCOVERY_V1_5.md): leitura temporal dos cinco candidatos com marcadores BEGIN/END, experimentos manuais de uma variável por vez e comparação de valores antes/durante/depois. São hipóteses experimentais, sem escrita em RAM e sem promoção automática de símbolos ao GoldenEye.mapping.

## Auto-Aim Memory Discovery v1.5.1 — Intervention Timing Audit

[Auditoria offline v1.5.1](docs/AUTOAIM_MEMORY_DISCOVERY_V1_5_1.md): mede distância entre transições e marcadores BEGIN/END, detecta alterações ocorridas antes do início e compara defasagens ON/OFF entre três offsets experimentais. Não modifica as capturas existentes nem estabelece causalidade ou endereços validados.

## Auto-Aim v1.6 — Semantic Consolidation

[Consolidação v1.6](docs/AUTOAIM_SEMANTIC_CONSOLIDATION_V1_6.md) registra a procedência canônica no `GoldenEye.mapping/experiments/` e inclui verificador offline. A exportação normal filtra estritamente `status=validated` para impedir que offsets experimentais ingressem no controle de mira. Não há Auto-Align ou Auto-Shot operacional.

## Auto-Aim Horizontal Correction Discovery v1

[Protocolo exploratório](docs/HORIZONTAL_CORRECTION_DISCOVERY_V1.md): oito snapshots RDRAM read-only para comparar alvo à esquerda/centro/direita com Auto-Aim ON/OFF e repetição independente da posição esquerda. Análise por byte produz **somente candidatos espaciais**, sem presunção de ângulo, endereço funcional ou comando de giro. Arquivos históricos e catálogos do GoldenEye.mapping permanecem preservados.

## Horizontal Correction Discovery v1.1 — Typed Interpretation

[Analisador offline v1.1](docs/HORIZONTAL_CORRECTION_DISCOVERY_V1_1.md) reinterpreta os 736 candidatos da sessão v1 em vizinhanças `int16/int32/float32`, big/little endian, sem novas capturas e sem substituir os arquivos v1. Nenhuma classificação estabelece ângulo, memória operacional ou Auto-Align.

## Horizontal Correction Discovery v1.2

[Temporal Candidate Validation](docs/HORIZONTAL_CORRECTION_DISCOVERY_V1_2.md): observador RDRAM read-only, dois candidatos de quatro bytes, marcadores BEGIN/END e relatório offline de transições, float32 LE apenas como hipótese. Sem símbolos validados, comandos de giro ou disparo.

## Horizontal Correction Discovery v1.3 — Camera/Aim Discrimination

[Protocolo v1.3](docs/HORIZONTAL_CORRECTION_DISCOVERY_V1_3.md): diferencia testes com câmera fixa e Auto-Aim ON/OFF de rotação de Bond sem alvo. Câmera fixa é condição declarada pelo operador (ainda sem sensor de heading validado). Observador read-only, análise temporal offline, sem controle automático.

## Horizontal Correction Discovery v1.4 — Directional Calibration

[Protocolo v1.4](docs/HORIZONTAL_CORRECTION_DISCOVERY_V1_4.md): comparação temporal de movimentos esquerdo/direito do alvo com câmera fixa, controles OFF e rotação manual de Bond. Capturas read-only, auditoria de sincronização e relatório explícito de encerramento da sessão; sem ângulos ou símbolos validados.

## Horizontal Correction Discovery v1.5 — Camera/Aim Separation

[Protocolo v1.5](docs/HORIZONTAL_CORRECTION_DISCOVERY_V1_5.md): capturas somente leitura em janelas candidatas e adjacentes alinhadas; comparação entre câmera fixa com mira acompanhando alvo e rotação de Bond sem alvo ou com Auto-Aim desligado. Relatórios imutáveis e encerramento auditável. Sem novos endereços presumidos nem controle automático.

## Horizontal Correction Discovery v1.5.1 — Timeline Integrity

[Procedimento v1.5.1](docs/HORIZONTAL_CORRECTION_DISCOVERY_V1_5_1.md): índices monotônicos de amostras, detecção de saltos e retrocessos do contador do emulador, registro de descontinuidades, encerramento seguro e análise por índice de amostra. A v1.5 e suas evidências permanecem intactas.

## Horizontal Correction Discovery v1.6 — Absolute Value & Context Audit

Implementados [coletor Lua v1.6](horizontal_correction_discovery_v1_6.lua), [envio de marcadores](tools/send_horizontal_v1_6.py), [auditoria de trajetórias absolutas e pares](tools/analyze_horizontal_v1_6.py), [testes de integridade](tests/test_horizontal_correction_discovery_v1_6.py) e [procedimento operacional](docs/HORIZONTAL_CORRECTION_DISCOVERY_V1_6.md). Preservação integral de amostras, inclusive frames estáveis; marcadores por índice monotônico; auditoria BE apenas hipotética; recusa de descontinuidades e de sessões incompletas. **Somente leitura; sem endereços de heading validados, sem Auto-Align/Auto-Shot e sem promoção automática ao GoldenEye.mapping.**

## Horizontal Correction Discovery v1.6.1 — Stationary Target Alignment

[Protocolo e comandos](docs/HORIZONTAL_CORRECTION_DISCOVERY_V1_6_1.md): câmera pode ser movimentada **apenas durante MANUAL_ALIGNMENT**, com inimigo parado; a fase STATIONARY_TARGET observa sem controles. Captura contínua e marcadores confirmados pela Lua, análise por fase e do hiato entre elas, sem inferir causalidade da correção da mira. Coletor: `horizontal_correction_discovery_v1_6_1.lua`; envio: `tools/send_horizontal_v1_6_1.py`; análise: `tools/analyze_horizontal_v1_6_1.py`; regressão: `tests/test_horizontal_correction_discovery_v1_6_1.py`. Somente leitura; novos endereços não são validados automaticamente.

## Spatial Target Alignment Discovery v1.7 — Bond Position Candidates

[Protocolo operacional](docs/SPATIAL_TARGET_ALIGNMENT_DISCOVERY_V1_7.md): [coletor read-only](spatial_target_alignment_discovery_v1_7.lua), [sender](tools/send_spatial_v1_7.py), [analisador](tools/analyze_spatial_v1_7.py) e [regressão](tests/test_spatial_target_alignment_v1_7.py). Captura snapshots completos da RDRAM de 8 MiB com Bond parado, deslocado, retornado e rotacionado; filtra hipóteses de campos float32 **sem presumir coordenadas ou endereços**. O reconhecimento de soldados e escolha do alvo mais próximo **ainda não estão implementados**. Arquivos de memória são locais e não devem ser publicados. Nenhuma escrita na memória, Auto-Align ou Auto-Shot.

## Spatial Candidate Cross-Session Validation v1.7.1

[Protocolo](docs/SPATIAL_CROSS_SESSION_VALIDATION_V1_7_1.md) e [analisador](tools/validate_spatial_cross_session_v1_7_1.py): cruzamento **sem limite Top-100** dos oito snapshots completos das sessões esquerda/direita da v1.7. Relatórios imutáveis de todos os candidatos que passam à triagem e sondas prioritárias mesmo quando reprovadas. Testes: `python -m unittest tests.test_spatial_cross_session_v1_7_1 -v`. Candidatos não confirmam posição física ou alvo Auto-Aim.

## Spatial Coordinate Candidate Validation v1.7.2

[Protocolo](docs/SPATIAL_COORDINATE_VALIDATION_V1_7_2.md) e [validador](tools/validate_spatial_coordinates_v1_7_2.py): refinamento dos relatórios da v1.7.1 usando filtros relativos de rotação/retorno, limiar de movimento, agrupamento de campos alinhados contíguos e padrões numéricos duplicados. Relatórios exclusivos, sem alterar dados de origem; testes: `python -m unittest tests.test_spatial_coordinates_v1_7_2 -v`. Coordenadas e Auto-Aim seguem não validados.

## Spatial Data Type Validation v1.7.3

[Protocolo](docs/SPATIAL_DATA_TYPE_VALIDATION_V1_7_3.md), [auditoria de bytes, floats e inteiros](tools/validate_spatial_data_types_v1_7_3.py) e [testes](tests/test_spatial_data_types_v1_7_3.py). Reutiliza oito snapshots v1.7 existentes com conferência dos manifestos; não sobrescreve relatórios anteriores. Compara RAW byte a byte, float32 e int32/uint32 nas endianidades big/little, retorno e rotação, preservando classificações descritivas. **Nenhum endereço, tipo de dado ou coordenada é validado automaticamente.**

## Spatial Position Confirmation v1.7.4

[Protocolo](docs/SPATIAL_POSITION_CONFIRMATION_V1_7_4.md), [coletor temporal read-only](spatial_position_confirmation_v1_7_4.lua), [sender](tools/send_spatial_v1_7_4.py), [analisador](tools/analyze_spatial_position_v1_7_4.py), [testes](tests/test_spatial_position_v1_7_4.py). Monitoramento de oito janelas RAW a cada frame com BEGIN/END para repouso, movimentos laterais, frente/trás e rotação, sem inventar offsets ou promover candidatos. Arquivos v1.7-v1.7.3 preservados; nenhuma escrita na memória, Auto-Align ou Auto-Shot.

## Temporal Event Correlation v1.7.5

[Protocolo](docs/TEMPORAL_EVENT_CORRELATION_V1_7_5.md), [analisador](tools/correlate_spatial_events_v1_7_5.py) e [testes](tests/test_temporal_event_correlation_v1_7_5.py): análise offline da captura v1.7.4, com validação de eventos contra o timeline RAW, distância aos marcadores, sincronização/defasagem entre os oito endereços, detecção de estados conjuntos recorrentes e sequências de transições repetidas. Sem novas capturas, sem escrita na memória e sem endereços de Bond ou Auto-Aim promovidos a confirmados.

## Spatial Position Discovery v1.8

[Protocolo experimental](docs/SPATIAL_POSITION_DISCOVERY_V1_8.md), [coletor de snapshots completos](spatial_position_discovery_v1_8.lua), [sender sequencial](tools/send_spatial_v1_8.py), [scanner RDRAM](tools/analyze_spatial_position_v1_8.py) e [testes](tests/test_spatial_position_discovery_v1_8.py). Retoma a procura pela posição física de Bond em toda a RDRAM de 8 MiB, utilizando 14 capturas etiquetadas manualmente de posições intermediárias, finais, repouso e rotação. Captura dependente da confirmação explícita do operador; não lê botões pressionados nem prova deslocamento por si só. Saídas experimentais e somente leitura; sem mapeamento ou geometria validada.

## Bond–Soldier Coordinate Correlation v1.8.2

[Protocolo experimental v1.8.2](docs/BOND_SOLDIER_COORDINATE_CORRELATION_V1_8_2.md): coletor `bond_soldier_coordinate_correlation_v1_8_2.lua` exclusivamente **read-only** registra os quatro campos candidatos de Bond (incluindo controles) e dois novos candidatos do Soldier #1 por frame, com aliases KSEG0/KSEG1 e marcadores controlados. `python -m tools.analyze_bond_soldier_v1_8_2 SESSION` identifica mudanças por frames efetivos, sem depender do marcador WRITE_APPLIED. Testes em `tests/test_bond_soldier_v1_8_2.py`. Nenhum eixo, offset do soldado ou localização física é considerado validado, e os arquivos da v1.3 permanecem intactos.

## Soldier Positive Motion Control v1.8.3

[Protocolo da v1.8.3](docs/BOND_SOLDIER_POSITIVE_MOTION_V1_8_3.md): `bond_soldier_positive_motion_v1_8_3.lua` observa os quatro campos candidatos de Bond e os dois campos experimentais do Soldier #1, sem escrita na RAM. Use `python -m tools.send_bond_soldier_v1_8_3 LABEL` para enviar marcadores sequenciais com confirmação `MARKED`. Após `DONE stop`, execute `python -m tools.analyze_bond_soldier_v1_8_3 SESSION`. O analisador compara Freeze, movimento positivo e reimobilização; **não valida automaticamente XYZ**. Testes sintéticos em `tests/test_bond_soldier_v1_8_3.py`. A v1.8.2 permanece preservada.

## Freeze Transition Timing & Soldier Coordinate Validation v1.8.4

[Protocolo](docs/BOND_SOLDIER_FREEZE_TRANSITION_V1_8_4.md). Novo observador `bond_soldier_freeze_transition_v1_8_4.lua` (somente leitura) acrescenta o indicador experimental u8 `0x02C90C` ao monitoramento Bond/Soldier, com leitura de aliases. Utilize `python -m tools.send_bond_soldier_v1_8_4 LABEL` para marcar os estados e `python -m tools.analyze_bond_soldier_v1_8_4 SID` para detectar episódios, pausas, transições do indicador e períodos de estabilidade. Os testes em `tests/test_bond_soldier_v1_8_4.py` são sintéticos, sem validação no BizHawk. **Não promove coordenadas nem Freeze a campos canônicos.**

## Soldier #1 Coordinate Discovery v1.8.5 — Bond-referenced full RDRAM search

[Protocolo](docs/SOLDIER_COORDINATE_DISCOVERY_V1_8_5.md). O novo coletor somente leitura `soldier_coordinate_discovery_v1_8_5.lua` tira snapshots RDRAM de 8 MiB em BASELINE, BOND_ROTATE, BOND_MOVE, SOLDIER_MOVE e SOLDIER_FREEZE, com NEW_SAVE opcional, mediante comandos atômicos de `python -m tools.send_soldier_coordinate_v1_8_5 LABEL`. O analisador `python -m tools.analyze_soldier_coordinate_v1_8_5 SID` procura campos float32 BE/LE alinhados que respondem a movimento de soldado mas não à rotação de Bond; proximidade com valores candidatos de Bond é apenas um filtro **não validado**. Binários são locais (`output/archive/`), sem exportar ROM/saves. Nenhuma descoberta de eixos X/Z, ponteiros ou estabilidade entre saves foi confirmada.

## Soldier Coordinate Discovery v1.8.6 — Spatial Structure Correlation

[Protocolo](docs/SOLDIER_SPATIAL_STRUCTURE_V1_8_6.md): observador `soldier_spatial_structure_v1_8_6.lua` (somente leitura) amostra por frame os endereços experimentais e suas vizinhanças de ±8 bytes nas famílias `0x06A1xx`, `0x1F19xx–0x1F1Bxx`, `0x20F4xx–0x20F7xx`, além de campos de referência da IA e Bond. Emissor: `python -m tools.send_soldier_spatial_v1_8_6 LABEL`; análise offline: `python -m tools.analyze_soldier_spatial_v1_8_6 SID`. Mede coocorrência de alterações, duplicação exata da série RAW e diferenças float32 BE hipotéticas; **não confirma X/Z, ponteiros, identidade do soldado ou persistência entre saves**. Testes sintéticos: `tests/test_soldier_spatial_v1_8_6.py`.

## Soldier Coordinate Discovery v1.8.7 — Entity Spatial Identity & Freeze Timing

[Protocolo](docs/SOLDIER_ENTITY_IDENTITY_V1_8_7.md): observador somente leitura `soldier_entity_identity_v1_8_7.lua`, emissor `tools/send_soldier_identity_v1_8_7.py` e analisador offline `tools/analyze_soldier_identity_v1_8_7.py`. Marcadores distintos para pedido, confirmacao visual e reversao do Freeze; pares duplicados e janelas retrospectivas de estabilidade. Testes sinteticos em `tests/test_soldier_identity_v1_8_7.py`. Identidade, XYZ e persistencia entre saves nao validadas.

## Soldier Coordinate Discovery v1.8.8 — Directional Axis Identification

[Protocolo v1.8.8](docs/SOLDIER_DIRECTIONAL_AXIS_V1_8_8.md): monitor read-only `soldier_directional_axis_v1_8_8.lua`, emissor `tools/send_soldier_direction_v1_8_8.py` e analisador `tools/analyze_soldier_direction_v1_8_8.py`. Compara respostas a direcoes opostas A+/A-, B+/B-, controles de rotacao/movimento de Bond e imobilidade. Testes `tests/test_soldier_direction_v1_8_8.py`. Direcoes sao anotacoes de operador, nao eixos de mundo validados. Nao promove offsets a simbolos.

## Soldier Coordinate Discovery v1.8.8.1 — AI Chase Observation

A v1.8.8 dependia de movimentos direcionais A/B do soldado que o operador nao controla. **Nao utilizar esse protocolo para validar eixos.** [Protocolo observacional substituto](docs/SOLDIER_CHASE_OBSERVATION_V1_8_8_1.md): `soldier_chase_observation_v1_8_8_1.lua`, `tools/send_soldier_chase_v1_8_8_1.py`, `tools/analyze_soldier_chase_v1_8_8_1.py`. Bond provoca perseguicao; o soldado so e observado. Coleta e analise sao somente leitura, sem atribuicao automatica X/Z ou identidade em RAM.

## Soldier Coordinate Discovery v1.8.8.2 — Bond proximity convergence

[Protocolo de convergencia](docs/SOLDIER_PROXIMITY_CONVERGENCE_V1_8_8_2.md) e analisador offline `tools/analyze_soldier_proximity_v1_8_8_2.py`: reusa capturas da v1.8.8.1, comparando a diferenca absoluta escalar entre candidatos de Bond e Soldier #1 durante `BOND_APPROACH` e `BOND_RETREAT`. Exige interpretacao cautelosa: aproximacao numerica nao prova distancia fisica 2D/3D, coordenadas mundiais ou identidade do soldado. Teste sintetico: `tests/test_soldier_proximity_v1_8_8_2.py`.

## Soldier Coordinate Discovery v1.8.9 — Dual-Axis Distance Convergence

[Análise offline e protocolo](docs/SOLDIER_DUAL_AXIS_DISTANCE_V1_8_9.md): `tools/analyze_soldier_dual_axis_v1_8_9.py` utiliza os CSVs existentes da v1.8.8.1 para calcular a distância candidata bidimensional **no mesmo frame** entre pares hipotéticos de Bond e Soldier #1. Compara configurações históricas, alternativas e aliases; não comprova eixos X/Z, distância física ou identidade de entidade. Testes sintéticos em `tests/test_soldier_dual_axis_v1_8_9.py`. Os endereços permanecem experimentais.

## Soldier Coordinate Discovery v1.8.10 — Frozen Soldier / Bond-only Motion

[Protocolo](docs/SOLDIER_FROZEN_BOND_MOTION_V1_8_10.md). Coletor `soldier_frozen_bond_motion_v1_8_10.lua` e emissor `tools/send_soldier_frozen_v1_8_10.py` anotam FREEZE confirmado visualmente, Bond aproximando/recuando, parada proxima/distante e rotacao sem translacao. Analisador `tools/analyze_soldier_frozen_v1_8_10.py` compara distancia hipotetica em dois componentes por frame e exige constancia dos campos do soldado durante todas as fases pos-Freeze para sinalizar convergencia controlada. Testes sinteticos em `tests/test_soldier_frozen_v1_8_10.py`. Ainda nao valida coordenadas fisicas X/Z, identidade ou estabilidade entre saves.

## Soldier Coordinate Discovery v1.8.11 — Auto-Aim Rotation Isolation

[Protocolo completo](docs/SOLDIER_AUTOAIM_ROTATION_V1_8_11.md): novo coletor `soldier_autoaim_rotation_v1_8_11.lua`, comandos `tools/send_soldier_autoaim_v1_8_11.py`, analisador `tools/analyze_soldier_autoaim_v1_8_11.py` e testes sintéticos. O analisador também aceita `--source v1.8.10` para decompor a rotação da sessão anterior, sem afirmar efeito causal do auto-aim. Estados auto-aim/Freeze são confirmados visualmente e não são controlados pelo script. Nenhuma validação definitiva de X/Z.

## Soldier Coordinate Discovery v1.8.12 — Rotation vs Translation

[Protocolo experimental](docs/SOLDIER_BOND_MOTION_V1_8_12.md): monitor somente leitura `soldier_bond_motion_v1_8_12.lua`, emissor `tools/send_soldier_motion_v1_8_12.py`, analisador `tools/analyze_soldier_motion_v1_8_12.py` e testes `tests/test_soldier_motion_v1_8_12.py`. Com Soldier #1 congelado, coleta rotação esquerda/direita, caminhada frente/trás e controles parados. Separa resposta por campo e fase, testa invariância dos candidatos do soldado e igualdade entre aliases. Não confirma direção física, auto-aim, XYZ nem identidade de entidade.
