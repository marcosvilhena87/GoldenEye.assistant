# Manual Controls Recognition v2.2 — Independent Trials

Mantém múltiplos testes simultâneos, cada um com `trial_id` imutável. Usa o perfil exportado de `GoldenEye.mapping`; não insere endereços, não altera memória e não injeta entradas.

## Preparação

Atualize o repositório no PowerShell. Se ainda não houver o arquivo `config/manual_controls_default.lua`, exporte-o com:

```powershell
python .\tools\export_manual_controls_v21.py ".\mapping_source"
```

Execute `manual_controls_v2_2.lua` na Lua Console, com a raiz do repositório como diretório de trabalho. **Encerre v2.1 antes**.

## Operação

No PowerShell da raiz do assistente:

```powershell
python .\tools\send_controls_v22.py PHASE gameplay
```

Pressione e solte Z, R, A e B no jogo. Observe os identificadores pendentes em `manual_controls_v2_2_pending.csv`:

```powershell
Import-Csv .\manual_controls_v2_2_pending.csv | Format-Table
```

Para um teste com ID 1 que comprovadamente disparou:

```powershell
python .\tools\send_controls_v22.py OBSERVED 1 fire_manual
python .\tools\send_controls_v22.py RESULT 1 yes
```

Para R, A, B, os valores observados quando efetivamente presentes no jogo são `visual_aim`, `cycle_weapon`, `reload`. O botão e a ação esperada são derivados do catálogo `default`. Use `RESULT ID no` ou `RESULT ID unknown` para falhas ou situações não conclusivas. Vários testes podem coexistir e ser concluídos fora da ordem de pressão. Não há associação implícita ao último controle.

## Arquivos

- `manual_controls_v2_2_events.csv`: transições brutas e ID atribuído ao PRESS.
- `manual_controls_v2_2_pending.csv`: **estado atual** dos testes ainda abertos; este arquivo é substituído pelo processo Lua.
- `manual_controls_v2_2_annotations.csv`: início de teste e declarações do operador.
- `manual_controls_v2_2_validation.csv`: confirmações por `trial_id`.
- `manual_controls_v2_2_diagnostics.csv`: erros, origem e estado da fila.
- `manual_controls_v2_2_inbox/000001.cmd`, etc.: comandos independentes gravados atomicamente; não editar manualmente.

O envio por arquivos independentes elimina o `Add-Content` concorrente no mesmo arquivo lido por NLua. Arquivos existentes ao iniciar são ignorados (apenas comandos novos são consumidos). Evite executar duas instâncias do detector ao mesmo tempo.

Um `RESULT yes` exige `OBSERVED` para o ID correto, e `operator_observed` não é `validated` automaticamente. Testes sem observação permanecem pendentes; não há expiração automática.

**Limitação:** o relatório de pendências é atualizado sobrescrevendo o mesmo arquivo; durante essa operação a leitura externa pode precisar ser repetida. A gravação da fila é atômica por arquivo, assumindo mesmo volume local e um único processo emissor.
