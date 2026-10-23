# Manual Controls Recognition v2.1

A v2.1 utiliza o perfil `default` de `GoldenEye.mapping/catalog/manual_controls.json`, exportado para Lua. Nenhum endereço de RAM é utilizado, nenhum comando é injetado.

## Preparação

Atualize os repositórios e execute na raiz do GoldenEye.assistant:

```powershell
python tools/export_manual_controls_v21.py "..\GoldenEye.mapping"
```

Ajuste o caminho caso o mapping esteja em outra pasta. Depois encerre a v2 e execute `manual_controls_v2_1.lua` pela Lua Console, com diretório de trabalho na raiz do assistente.

## Fluxo (um teste por vez)

```powershell
Add-Content .\manual_controls_v2_1_commands.txt "PHASE:gameplay"
```

Pressione **Z** uma vez e solte. O detector abre um teste e obtém `fire_manual` do perfil canônico. Confirme o efeito que observou em jogo:

```powershell
Add-Content .\manual_controls_v2_1_commands.txt "OBSERVED:fire_manual"
Add-Content .\manual_controls_v2_1_commands.txt "RESULT:yes"
```

Para R, A e B, utilize `OBSERVED:visual_aim`, `OBSERVED:cycle_weapon`, `OBSERVED:reload`, respectivamente, se tais efeitos ocorreram. Para falha observada use `RESULT:no`, e na dúvida `RESULT:unknown`; valores aceitos são yes/no/unknown. Grave `RESULT` antes de pressionar outro botão conhecido; caso contrário o teste antigo fica inconclusivo. `NOTE:...` registra observações.

## Arquivos CSV

- `manual_controls_v2_1_events.csv`: press/release e mudanças analógicas.
- `manual_controls_v2_1_annotations.csv`: contexto e observação do operador.
- `manual_controls_v2_1_validation.csv`: session,trial_id,press_frame,report_frame,phase,profile,source,control,expected_action,observed_action,result,match,status,notes.
- `manual_controls_v2_1_diagnostics.csv`: fonte de entrada, baseline e erros.

Um resultado positivo é rotulado `operator_observed`, e não `validated`: o código não lê o efeito do jogo e não valida automaticamente munição ou mira. A identidade da ROM e o layout interno selecionado continuam pendentes.
