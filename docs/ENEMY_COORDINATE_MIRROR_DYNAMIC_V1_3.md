# Enemy Coordinate Discovery v1.3 — Memory Mirror & Dynamic Field Analysis

## Base
v1.2 confirmou experimentalmente na sessão `20261024T210536Z_648577` que, na janela A `[0x0D5000,0x0D8500)`, a comparação com `A+0x11800` apresentou 10.409/13.568 bytes iguais em P1 (76,72%) e 10.700/13.568 em P2 (78,86%), muito acima dos seis controles próximos (15–29%). Foram observadas 10.143 igualdades nas duas épocas e 823 bytes com mudança de igualdade. São evidências da captura fornecidas pelo operador, **não comprovação de coordenadas**.

## Método
O analisador v1.3 inspeciona os quatro dumps ON/ON HOLD de P1 e P2, em uma janela original fixa `[0x0D5000,0x0D8500)`, e a janela B deslocada por `0x11800`. Cada byte é analisado **uma vez**, independentemente de big/little endian. O script mede:
- Bytes sempre zero em cada região e em ambas.
- Igualdade A/B em P1, P2 e em todas as quatro capturas.
- Estabilidade de A em cada época ON (stable versus hold), idem para B.
- Mudança entre P1 e P2 por região, exigindo estabilidade ON de ambos os lados para uma linha dinâmica.
- Campos dinâmicos espelhados (A e B com todos os quatro valores iguais) e distintos (pelo menos uma diferença).
- Trechos contíguos de bytes dinâmicos classificados em mirrored/distinct; trechos **não são** limites demonstrados de campos ou objetos.

Cada arquivo binário de entrada deve ter 8 MiB, a proveniência exige metadados same-frame, estado ON e etiqueta de hipótese KSEG0. Não há escrita em RAM nem alteração de dumps existentes.

## Execução
```powershell
git pull --ff-only origin main
python -m unittest tests.test_enemy_freeze_v1_3 -v
$sid="20261024T210536Z_648577"
python -m tools.analyze_enemy_freeze_v1_3 $sid
```

## Arquivos gerados
Em `output/csv`, prefixo `enemy_freeze_v1_3_<sid>`:
- `dynamic_fields.csv`: offsets A/B, estabilidade, mudança, igualdade P1/P2 e quatro bytes brutos de cada lado (ordem: P1, P1 HOLD, P2, P2 HOLD).
- `dynamic_runs.csv`: trechos contíguos dos bytes dinâmicos, classificados como mirrored ou distinct.
- `summary.json`: totais, parâmetros, arquivos de origem, ressalvas.

Todos são gerados em modo de criação exclusiva: não sobrescrever relatórios anteriores.

## Limitações e próximos controles
A análise usa somente duas épocas ON, não possui terceira posição congelada, trajetória física ou identidade de inimigo. Não consegue diferenciar espelhamento permanente de conteúdo incidentalmente igual em quatro snapshots. Byte zero pode fazer parte de um valor multibyte; a filtragem é contábil e não elimina campos. `dynamic_fields` enumera bytes, não coordenadas float32 validadas. Para avançar, testar P3, direção de movimento, mutações OFF e comparar outra sessão ROM/core. Não promover símbolos no `GoldenEye.mapping`.
