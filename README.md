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
