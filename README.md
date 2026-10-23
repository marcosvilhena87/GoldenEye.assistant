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
