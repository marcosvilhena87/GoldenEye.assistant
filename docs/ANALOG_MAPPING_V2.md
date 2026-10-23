# Analog Mapping v2 — Sensibilidade e Deadzone (fase experimental)

**Escopo:** entradas `X Axis`/`Y Axis` da porta 1 via `joypad.getimmediate` (fallback para `get` e `getwithmovie`). Sem injeção, escrita RAM ou endereços presumidos. **Deadzone da API e deadzone efetiva do jogo são grandezas distintas**; a segunda não é medida automaticamente por este detector.

## Preparação
1. Pare todos os scripts anteriores no BizHawk. Na raiz de `GoldenEye.assistant`, execute `python tools/prepare_output.py`.
2. Abra `analog_mapping_v2.lua` na Lua Console, mantendo a raiz como diretório de trabalho.
3. Confirme `output/sessions/analog_v2_session.txt` e `output/csv/analog_v2_diagnostics.csv`.

## Protocolo recomendado
Execute `python .\tools\send_analog_v2.py PHASE neutral_start`; mantenha o analógico solto por alguns segundos. Em seguida, uma fase de cada vez, marque **antes** de mover, mova vagarosamente em incrementos aproximados e mantenha o controle parado. Solte ao centro antes da fase seguinte.

- `small_x`: faça deslocamentos mínimos para esquerda/direita a partir de zero, procurando o menor valor não zero registrado.
- `small_y`: equivalente acima/abaixo.
- `x_low`, `x_mid`, `x_high`: deflexões horizontais baixa, média, alta, mantendo cada posição.
- `y_low`, `y_mid`, `y_high`: deflexões verticais baixa, média, alta.
- `neutral_end`: solte e mantenha centralizado.
- Use `NOTE` para registrar por escrito algum movimento visível de Bond, mas **não** conclua o limiar da deadzone de jogo a partir dos eixos apenas.

Comando exemplo: `python .\tools\send_analog_v2.py PHASE small_x`. Verifique mudança de fase no diagnóstico antes de iniciar a deflexão. Não envie todos os comandos em um único bloco sem realizar os movimentos.

O detector grava uma linha quando os eixos mudam e também uma amostra periódica a cada 10 frames. Isso permite calcular permanência, dispersão e transições intermediárias, não apenas extremos. O CSV `analog_v2_samples.csv` contém sessão, frame, fase, fonte, tipo de amostra, X, Y e magnitude `sqrt(X²+Y²)`. Consulte:

```powershell
python .\tools\analyze_analog_v2.py
Get-Content .\output\csv\analog_v2_diagnostics.csv -Tail 20
```

Um valor inteiro `0` pode ser efeito da configuração de deadzone do controle mapeado no BizHawk; não implica ausência de pequenas deflexões físicas. Também não permite medir automaticamente o limiar interno de movimento do GoldenEye. Para isso, haverá teste funcional separado com ação observada na tela ou futura variável validada no mapping.

Após o teste, forneça `analog_v2_samples.csv` e `analog_v2_diagnostics.csv` para interpretação e eventual registro no `GoldenEye.mapping` como observado.
