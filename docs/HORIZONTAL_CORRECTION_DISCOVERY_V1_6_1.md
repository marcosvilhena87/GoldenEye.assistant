# Horizontal Correction Discovery v1.6.1 — Stationary Target Alignment

## Finalidade

Permitir um **ajuste manual inicial da câmera** para enquadrar um **inimigo parado**, seguido de uma fase estacionária sem controles. A captura de bytes da RDRAM permanece **contínua**, mas as fases são isoladas por marcadores. Nenhuma orientação da arma/câmera é considerada identificada. Todas as operações são somente leitura.

## Preparação

1. Atualizar o repositório, preparar `output/csv`, `output/commands`, `output/sessions`.
2. Em `horizontal_correction_discovery_v1_6_1.lua`, configurar `DOMAIN="RDRAM"` e `EXPECTED_SIZE=8388608` **apenas se confirmados no BizHawk**. Por padrão ficam `nil`.
3. Localizar um inimigo parado. Escolher a condição (Auto-Aim ON/OFF) antes de iniciar; não alternar opções durante a janela.
4. Executar o script no Lua Console. Anotar a nova sessão em `output/sessions/horizontal_v1_6_1_session.txt`.
5. Nunca carregar savestate **dentro** da mesma captura: um salto de frames dispara encerramento por descontinuidade. Para replay via savestate, carregar primeiro, **então** iniciar uma nova instância Lua/sessão.

## Sequência de uma captura (Auto-Aim ON, inimigo parado)

```powershell
python .\tools\send_horizontal_v1_6_1.py BEGIN_MANUAL_ALIGNMENT
# Aguardar: [horizontal.v1.6.1] marked BEGIN_MANUAL_ALIGNMENT
# Ajustar manualmente a câmera com inimigo parado na lateral do campo de visão.
python .\tools\send_horizontal_v1_6_1.py END_MANUAL_ALIGNMENT
# Aguardar confirmação END; soltar todos os controles.

python .\tools\send_horizontal_v1_6_1.py BEGIN_STATIONARY_TARGET
# Aguardar confirmação; observar arma sem mover Bond/câmera.
python .\tools\send_horizontal_v1_6_1.py END_STATIONARY_TARGET
# Aguardar confirmação END.
python .\tools\send_horizontal_v1_6_1.py STOP
# Aguardar FINISHED reason=stop active_action=nil/NONE.
```

**Importante:** cada comando `Request created` só significa que entrou na fila. Confirmar `marked` na Lua **antes** de intervir ou enviar o próximo. `END_MANUAL_ALIGNMENT` deve ser emitido após concluir o ajuste, sem iniciar outro movimento. Se a arma já corrigiu durante a intervenção manual, não atribuir essa mudança ao Auto-Aim.

Repetir com alvo à esquerda, alvo à direita e Auto-Aim OFF; usar **nova sessão** para cada restauração de savestate. Quando OFF, usar `BEGIN_STATIONARY_TARGET_AIM_OFF` e `END_STATIONARY_TARGET_AIM_OFF` no lugar da fase estacionária. Registrar externamente posição/cena, lado do alvo, configuração ON/OFF e se houve correção visível.

## Auditoria

```powershell
$session = (Get-Content .\output\sessions\horizontal_v1_6_1_session.txt -Raw).Trim()
python .\tools\analyze_horizontal_v1_6_1.py $session
Import-Csv ".\output\csv\horizontal_v1_6_1_${session}_pair_audit.csv" | Format-Table -AutoSize
Import-Csv ".\output\csv\horizontal_v1_6_1_${session}_phase_comparison.csv" | Format-Table -AutoSize
```

A v1.6.1 gera três relatórios imutáveis:
- `_absolute_audit.csv`: trajetória RAW e interpretação float32 BE hipotética por fase.
- `_pair_audit.csv`: sincronização e `B-A` em **todas as amostras**.
- `_phase_comparison.csv`: diferença entre o último valor da fase manual e o primeiro valor da fase estacionária; indica quantas amostras existem no intervalo entre os marcadores. Esse hiato **não é prova de correção por Auto-Aim**.

Preserva `_timeline.csv`, `_events.csv`, `_markers.csv`, `_termination.csv`, `_discontinuities.csv`, `_manifest.csv`. Análises abortam em sessões incompletas ou descontinuadas. Nunca promover candidatos a símbolos validados automaticamente.

## Regressão

```powershell
python -m unittest tests.test_horizontal_correction_discovery_v1_6_1 -v
python -m unittest discover -s tests -v
```
