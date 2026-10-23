# Manual Controls Recognition v2

**Pré-requisito:** v1 identificou controles, fontes NLua expostas como `userdata` e captura por frame. A v2 é **somente observação**; não infere função do botão pelo nome, não lê RAM e não envia inputs. Não executar v1 e v2 simultaneamente.

## Executar
1. `git pull --ff-only origin main` no checkout GoldenEye.assistant.
2. No BizHawk Lua Console, com diretório de trabalho apontando para a raiz do repositório, abrir `manual_controls_v2.lua`.
3. Em um segundo PowerShell na mesma pasta, anotar a ação **antes** de apertar o botão, por exemplo:
   ```powershell
   Add-Content .\manual_controls_v2_commands.txt "ACTION:fire_manual"
   Add-Content .\manual_controls_v2_commands.txt "EXPECT:Z"
   ```
4. Acionar Z sozinho, soltar, repetir; registrar observação da tela: `Add-Content .\manual_controls_v2_commands.txt "NOTE:Bond fired once"`. Para o próximo teste, escrever `ACTION:aim_manual`, `EXPECT:R`; testar demais botões isoladamente. `PHASE:gameplay` ou `PHASE:menu` marca contexto. `RESET:` reinicia anotações.

Ação informada em `ACTION` representa **hipótese do operador**, não evidência automática de efeito no jogo. `EXPECT` é o controle esperado, separado do controle realmente lido.

## Saídas CSV
- `manual_controls_v2_events.csv`: uma linha **somente quando muda um botão/eixo**, com `session,frame,phase,action,port,source,control,event,old_value,new_value`.
- `manual_controls_v2_annotations.csv`: `session,frame,phase,action,expected_control,kind,detail`.
- `manual_controls_v2_diagnostics.csv`: `session,frame,code,detail`.

Ao contrário da v1, não gera amostras repetitivas para todos os controles em todos os frames. Observe que mudanças ocorridas no mesmo frame que a troca de rótulo serão associadas ao novo rótulo: marque antes de pressionar. A leitura prioriza `getimmediate`, então `get`, depois `getwithmovie` (apenas uma fonte por sessão de leitura), e explicita fonte e mudanças de origem. A v2 não registra ações inferidas ou confirma mapeamentos no catálogo canônico sem replicação.

## Testes sugeridos
Baseline sem toque; analógico X e Y em direções separadas; Z, R, A, B, L, Start e C individuais; combinação R+Z; soltura; repetição em gameplay e menu. Registrar controles observados e significado efetivo no jogo; configurações de controle GoldenEye podem mudar o significado.

## Critério para v3
Somente promover a relação controle→ação quando confirmada visualmente em múltiplas repetições, associada ao layout/configuração do jogo. Endereços de memória continuam exclusivos de GoldenEye.mapping.
