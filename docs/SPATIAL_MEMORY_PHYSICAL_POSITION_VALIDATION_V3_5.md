# Spatial Memory Physical Position Validation v3.5

## Finalidade

Investigar se valores reais da janela `0x3B30B0–0x3B30FF`, registrados pelo coletor v2.4, exibem o comportamento necessário de uma **coordenada candidata**: mudança na ida, inversão na volta, retorno próximo de P0, estabilidade sob rotação sem deslocamento e nova mudança após avançar em outra orientação.

Esta etapa não converte correlação de mudanças em prova de posição física. Não dispomos de coordenadas externas medidas ou da distância/ângulo reais de Bond. Por isso o programa classifica apenas `cross_session_candidate` ou `not_supported`; **jamais** `validated_coordinate`.

## Executar

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_physical_v3_5 -v

$original='20261024T152944Z_311185'
$replica='20261024T171358Z_645378'
$third='20261024T182827Z_912356'

python .\tools\analyze_spatial_physical_v3_5.py $original $replica $third
```

A carga de memória é considerável (80 bytes × muitos frames por sessão), e o analisador processa os CSVs no computador local. `load` valida STOP, ordem das fases, completude por frame e descontinuidades.

## Critérios de triagem, definidos antes desta execução

Para todos os offsets alinhados de 4 bytes e interpretações `be_f32`, `le_f32`, `be_i32` e `be_u32`:

- Medianas e desvios absolutos medianos dos **últimos 120 frames** de P0_HOLD, P1_HOLD, P0_RETURN_HOLD, P0_ROTATED_HOLD e P2_HOLD.
- Mudanças de ida, volta e segundo avanço devem superar tanto `1e-6` quanto 10 vezes o maior MAD das paradas.
- Passo ida × passo volta negativo (sinais inversos).
- Erro de retorno relativo <=10% da maior variação.
- Desvio relativo por rotação sem movimento <=10%.
- MAD máximo <=2% da maior variação.
- Uma candidata intersessão deve cumprir todos os critérios em **todas** as sessões fornecidas, com a mesma interpretação dos 4 bytes.

O resultado `_axis_pairs.csv` combina pares de candidatos em offsets diferentes e indica se os vetores de variação entre o primeiro e o segundo movimento não são colineares (`>=0.1` na razão de determinante normalizado usada). Não prova que sejam X/Y ou componentes de um sistema cartesiano. Paradas controladas, ângulos e distâncias **não são verificáveis automaticamente** com estes arquivos.

## Saídas

- `_hold_differentials.csv`: uma linha por sessão × offset × interpretação;
- `_cross_session.csv`: uma linha por offset × interpretação, com decisões conservadoras;
- `_axis_pairs.csv`: avaliação auxiliar dos pares entre possíveis eixos.

Os arquivos nunca são sobrescritos. Não edite capturas nem altere o catálogo `GoldenEye.mapping`.

## Consultar resultados

```powershell
Import-Csv ".\output\csv\spatial_v3_5_${original}__${replica}__${third}_cross_session.csv" |
 Where-Object { $_.decision -eq 'cross_session_candidate' } |
 Select-Object offset,kind,passed,sessions,worst_return_error_ratio,worst_rotation_error_ratio,worst_hold_mad_ratio |
 Format-Table -AutoSize
```

## Interpretação correta

Uma coordenada **real** exigirá posteriormente calibração externa independente: distância/direção observável, movimento controlado em pelo menos dois eixos, retorno, rotação no lugar e distinção de câmera versus Bond. Mesmo uma candidata que passe em três sessões pode ser velocidade, animação, variável de câmera ou um campo derivado e não pode ser promovida como coordenada canônica.
