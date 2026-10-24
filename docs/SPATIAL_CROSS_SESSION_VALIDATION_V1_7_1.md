# Spatial Candidate Cross-Session Validation v1.7.1

## Objetivo
Cruzar **diretamente os oito snapshots completos** das sessões v1.7, sem depender dos relatórios Top-100. O resultado continua composto por **candidatos experimentais**, não coordenadas estabelecidas de Bond.

## Capturas já disponíveis (no computador do operador)
- Esquerda: `20261024T012117Z_46365`
- Direita: `20261024T012527Z_57819`

As capturas devem existir em `output/archive/` com CSVs de manifesto em `output/csv/`. Se o estado de Bond, o cenário e a câmera não eram equivalentes nas duas sessões, a interpretação dos sinais opostos ou iguais é limitada. Retornar visualmente à mesma posição não comprova igualdade física exata.

## Executar no PowerShell

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_cross_session_v1_7_1 -v
python .\tools\validate_spatial_cross_session_v1_7_1.py 20261024T012117Z_46365 20261024T012527Z_57819
```

Saídas imutáveis:
- `output/csv/spatial_v1_7_1_20261024T012117Z_46365_vs_20261024T012527Z_57819_cross_candidates.csv`
- `output/csv/spatial_v1_7_1_20261024T012117Z_46365_vs_20261024T012527Z_57819_priority_probes.csv`

A primeira contém **todos** os campos alinhados de quatro bytes que passam aos filtros em uma ou nas duas sessões, incluindo interpretações float32 big/little-endian. Não há corte Top-100. A segunda inspeciona incondicionalmente, nas duas endianidades, os endereços `0x3B2BD4`, `0x3B2BD8`, `0x3B2BDC`, `0x1F1E88`, `0x1F1E8C`, `0x1F1E90`, `0x05FCB4`, `0x05FCD4`, `0x2EBCE4`, ainda que reprovados.

```powershell
$left='20261024T012117Z_46365'
$right='20261024T012527Z_57819'
$prefix=".\output\csv\spatial_v1_7_1_${left}_vs_${right}"
Import-Csv "${prefix}_priority_probes.csv" |
  Select-Object offset_hex,endianness,delta_left,delta_right,left_pass,right_pass,classification |
  Format-Table -AutoSize
Import-Csv "${prefix}_cross_candidates.csv" |
  Group-Object classification | Select-Object Name,Count | Format-Table -AutoSize
```

## Critérios e limitações
A análise percorre a RDRAM inteira em offsets múltiplos de 4, mas **não** explora campos desalinhados, formatos inteiros, vetores comprimidos nem structs por ponteiro. Campos float32 finitos com módulo superior a 1e6 são rejeitados na triagem. Movimento deve provocar magnitude no intervalo (0.00001, 100000). O retorno e a rotação devem divergir do baseline abaixo dos limites relativos/absolutos do analisador v1.7. Esses limites são heurísticos, não propriedades do jogo.

As categorias significam:
- `opposite_sign_unverified`: aprovado em ambas as sessões com sinais diferentes;
- `same_sign_unverified`: aprovado nas duas sessões, mesmo sinal;
- `one_session_only_unverified`: aprovado apenas em uma;
- `fails_filters_or_inconclusive`: presente no arquivo de sondas prioritárias, mas não aprovado.

A ordenação prioriza aprovados em ambas as sessões, depois sinais opostos; isso **não** equivale a promover endereços a coordenadas. Não compare a identidade numérica do baseline entre sessões sem verificar equivalência das cenas, e não interprete a variação de X/Y/Z sem eixo, sinal e escala confirmados.

O programa valida CSV de snapshots, sessões encerradas, arquivos binários de tamanho esperado, marcadores e ausência de descontinuidade. Não altera Lua, ROM ou memória do jogo, não carrega o estado salvo e não publica dumps. Reexecutar com o mesmo nome de sessões recusa sobrescrever os CSVs anteriores.

## Próximo passo
Se os campos prioritários não se reproduzirem, preparar capturas adicionais com deslocamentos ortogonais, aproximação medida e observação visual da posição. A busca por coordenadas de soldados, soldado mais próximo e correção Auto-Aim permanece pendente até termos um referencial Bond validado.
