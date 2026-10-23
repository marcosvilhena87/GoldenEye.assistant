# Analog Mapping v1 — GoldenEye 007 N64

Captura **valores brutos** de `X Axis` e `Y Axis` (porta 1) por frame e por fase nomeada. É separado do Manual Controls Recognition v2.2.1. Não presume faixa, sinal, deadzone, velocidade ou efeito de gameplay; não escreve RAM e não injeta inputs.

## Execução

1. Atualize o repositório e encerre os observadores anteriores na Lua Console do BizHawk.
2. Abra `analog_mapping_v1.lua` na Lua Console com a raiz de `GoldenEye.assistant` como diretório de trabalho.
3. Com analógico centralizado, execute no PowerShell:

```powershell
python .\tools\send_analog_v1.py PHASE neutral
```

4. Em seguida movimente o analógico **uma direção por vez**, usando `PHASE` *antes* de mover, segurando durante alguns segundos e retornando ao centro antes da próxima fase. Registre as fases sugeridas nesta ordem: `up`, `down`, `left`, `right`, `up_left`, `up_right`, `down_left`, `down_right`, `neutral_end`.

Exemplo:

```powershell
python .\tools\send_analog_v1.py PHASE up
```

Espere a fase aparecer nos diagnósticos e então mova o analógico para cima; mantenha-o por alguns segundos e solte. Prossiga com as outras direções, uma de cada vez. Também pode registrar `NOTE` para marcar comportamentos visíveis. Teste primeiro em gameplay parado, sem apertar outros botões.

## Saídas
- `analog_v1_samples.csv`: session,frame,phase,source,kind,x_axis,y_axis; escreve a linha inicial (`BASELINE`), mudanças (`CHANGE`) e uma leitura na troca de fase (`PHASE_SNAPSHOT`).
- `analog_v1_diagnostics.csv`: início, mudanças de fonte, mudança de fase e indisponibilidade de eixo.
- `analog_v1_session.txt`: ID de sessão ativa.
- `analog_v1_inbox/SESSION/*.cmd`: comandos publicados por arquivo atômico, isolados por sessão.

**Atenção:** essa etapa só valida os eixos lidos pelo BizHawk. A relação com andar, olhar, virar e mirar exige observações de gameplay posteriores. A nomenclatura `X Axis` e `Y Axis` é da API de controle, não um endereço de memória do GoldenEye.
