# Spatial Position Discovery v2.4 — Controlled Movement Differential Discovery

**Objetivo:** comparar posições estáticas depois de movimentos manuais controlados; evitar a inferência por taxas brutas de mudança. Os 80 bytes da janela `0x3B30B0–0x3B30FF` continuam **experimentais**, sem validação de coordenadas. Essa etapa exige **nova sessão** no BizHawk; os CSVs anteriores permanecem inalterados.

## Preparação

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_position_discovery_v2_4 -v
python .\tools\prepare_output.py
```

No `spatial_position_discovery_v2_4.lua`, configure manualmente os valores **após verificar o domínio do BizHawk**:

```lua
local DOMAIN="RDRAM"
local EXPECTED_SIZE=8388608
```

Carregue `spatial_position_discovery_v2_4.lua` na sessão em andamento. Não carregue savestates ou reinicie o script até STOP confirmado. O protocolo manual tem esta ordem, **um comando de cada vez, esperando `marked`**:

| Marcador | Operação após reconhecimento do marcador |
|---|---|
| `P0_HOLD` | Bond parado no ponto inicial |
| `FORWARD` | Avançar em linha reta sem girar |
| `P1_HOLD` | Parar e ficar imóvel no novo ponto |
| `BACK` | Recuar tentando voltar exatamente ao ponto inicial |
| `P0_RETURN_HOLD` | Permanecer imóvel depois do recuo |
| `ROTATE` | Girar horizontalmente, sem deslocamento |
| `P0_ROTATED_HOLD` | Permanecer imóvel após a rotação |
| `FORWARD_AGAIN` | Avançar novamente na nova direção |
| `P2_HOLD` | Permanecer imóvel no novo ponto |
| `STOP` | Finalizar |

Todos os períodos HOLD devem ter **pelo menos 120 frames**. Os marcadores identificam as fases, mas não confirmam os comandos físicos executados. **A rotação altera o rumo**, então `P2_HOLD` não precisa reproduzir a coordenada de `P1_HOLD`; isso é usado apenas para examinar reação em novo rumo.

Cada linha abaixo deve ser executada separadamente no momento adequado; nunca enviar tudo em sequência:

```powershell
python .\tools\send_spatial_v2_4.py P0_HOLD
python .\tools\send_spatial_v2_4.py FORWARD
python .\tools\send_spatial_v2_4.py P1_HOLD
python .\tools\send_spatial_v2_4.py BACK
python .\tools\send_spatial_v2_4.py P0_RETURN_HOLD
python .\tools\send_spatial_v2_4.py ROTATE
python .\tools\send_spatial_v2_4.py P0_ROTATED_HOLD
python .\tools\send_spatial_v2_4.py FORWARD_AGAIN
python .\tools\send_spatial_v2_4.py P2_HOLD
python .\tools\send_spatial_v2_4.py STOP
```

Após `[spatial.v2.4] FINISHED ... reason=stop`:

```powershell
$session=(Get-Content .\output\sessions\spatial_v2_4_session.txt -Raw).Trim()
python .\tools\analyze_spatial_position_v2_4.py $session
Import-Csv ".\output\csv\spatial_v2_4_${session}_differentials.csv" |
 Where-Object { $_.status -eq 'experimental_candidate' } |
 Select-Object offset,width,type,step1,step_back,return_error,rotation_shift,step2,holds_stable |
 Format-Table -AutoSize
```

O analisador usa a mediana e o desvio absoluto mediano (MAD) dos **últimos 120 frames** de cada HOLD. Rejeita sessões incompletas, marcos inválidos, ausências de bytes e interrupções temporais. Analisa campos alinhados de 16 e 32 bits, diferenciando interpretações de inteiros e float32.

**Atenção:** o estado `experimental_candidate` apenas passa pelos filtros heurísticos (movimento, retorno, estabilidade, rotação). Não confirma coordenadas; exige reprodução independente, controle de cenário e alinhamento entre movimento e campos. Os limites de estabilidade são arbitrados para triagem e não uma validação definitiva. Se nenhum campo passar, os endereços seguem não validados.
