# Spatial Memory Confirmatory Protocol v3.4

## Objetivo

Protocolo **pré-especificado no código** para avaliar uma **terceira captura independente** do GoldenEye 007. Não se trata de confirmação estatística retroativa das duas primeiras capturas e não identifica coordenadas ou ponteiros.

## Registro antes da nova captura

Antes de iniciar o BizHawk, execute:

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_confirmation_v3_4 -v
python .\tools\analyze_spatial_confirmation_v3_4.py --show-protocol
git rev-parse HEAD
```

Registre o hash exibido por `--show-protocol` e o SHA do commit; não altere o protocolo depois de ver os dados. Os endereços foram selecionados exploratoriamente das sessões 1 e 2; o ensaio com a terceira sessão testa uma hipótese previamente congelada, mas não elimina dependências e multiplicidade.

### Hipóteses fixadas

| Prioridade | Origem | Alvo | Objetivo |
|---|---|---|---|
| Primária | `0x3B30E0` | `0x3B30E4` | Ganho de acurácia e log-loss positivos em ao menos 7/9 fases |
| Secundária | `0x3B30BC` | `0x3B30C4` | Diagnóstico |
| Secundária | `0x3B30D0` | `0x3B30E0` | Comparação histórica |
| Diagnóstica | `0x3B30BC` | `0x3B30C0` | Ganho de acurácia elevado / log-loss adverso |

Treinamento fixo **apenas** na primeira sessão: `20261024T152944Z_311185`. A segunda sessão `20261024T171358Z_645378` foi usada para seleção de hipóteses e não entra no teste confirmatório. A terceira sessão não é usada para retreinar, selecionar candidatos nem ajustar limiares.

### Protocolo de captura

Execute o coletor **v2.4 existente** com `DOMAIN="RDRAM"`, tamanho validado de 8 MiB e limite de frames suficiente, sem modificar o script durante a execução. Capture as dez marcações em sequência, aguardando `marked` antes de cada ação:

`P0_HOLD → FORWARD → P1_HOLD → BACK → P0_RETURN_HOLD → ROTATE → P0_ROTATED_HOLD → FORWARD_AGAIN → P2_HOLD → STOP`.

Mantenha **ao menos 120 frames por fase**, incluindo as paradas; para comparar movimentos, preserve o mesmo mapa/situação e trajetórias deliberadas quando possível. Não há verificação automatizada de amplitude/distância/ângulo porque esses controles não foram instrumentalizados. Evite pausar, reiniciar ou reusar ID de sessão; não altere dados brutos.

O utilitário de marcação é `python .\tools\send_spatial_v2_4.py <LABEL>`, substituindo LABEL pela próxima fase; capture o ID que o coletor imprimir. Sempre confira o reconhecimento `marked LABEL` no Lua antes do próximo envio.

### Avaliar após STOP confirmado

```powershell
$third = '<ID_DESTA_NOVA_SESSAO>'
python .\tools\analyze_spatial_confirmation_v3_4.py $third
Import-Csv ".\output\csv\spatial_v3_4_${third}_pair_summary.csv" | Format-Table -AutoSize
```

Validação de integridade reutiliza `load` da v2.4: STOP, nenhuma descontinuidade, 80 bytes por frame, sequência ordenada e todas as fases. Rejeita sessões 1 e 2, fases com menos de 120 frames e resultados já existentes. Outputs: `_phase_results.csv` (36 linhas), `_pair_summary.csv` (4 linhas) e `_protocol.json` (cópia com SHA256 do protocolo).

O critério **primário** exige em pelo menos sete fases ganho de acurácia >=0,02 e melhora positiva de log-loss, além de ganhos médios de acurácia e log-loss positivos. Controles por 99 deslocamentos circulares em cada fase geram p empírico **descritivo**, sem correção por multiplicidade e sem reivindicar significância estatística. Não se calcula um teste formal de nível alfa.

`primary_criteria_met` significa exclusivamente que os **critérios descritivos predefinidos** foram satisfeitos; **não** significa prova de coordenada física ou estrutura. Publicar resultados positivos e negativos, inclusive falhas de captura, e evitar ajustar limiares após observar o resultado.

O catálogo `GoldenEye.mapping` não deve ser alterado sem validação espacial direta.
