# Horizontal Correction Discovery v1.6 — Absolute Value & Context Audit

Esta versão mantém a captura experimental **somente leitura** da v1.5.1, a verificação de sequência de frames, marcadores por `sample_index`, a rejeição de sobrescrita e a separação entre evidência e função semântica.

## Objetivo
Testar se as oito janelas RAW observadas (incluindo `0x0D3998` e `0x0D3D40`) respondem a mira, ausência de alvo e rotação manual. **Não presumir** `camera_heading`, `weapon_heading`, Auto-Aim Correction, float, sinal ou escala.

## Configurar e iniciar
1. No `horizontal_correction_discovery_v1_6.lua`, configurar `DOMAIN="RDRAM"` e `EXPECTED_SIZE=8388608` **somente após conferir domínio e tamanho no BizHawk**. Estes parâmetros ficam `nil` por padrão.
2. Garantir as pastas `output/csv/`, `output/commands/`, `output/sessions/`. Executar os preparativos do repositório se necessário.
3. Carregar o coletor v1.6 no Lua Console; copiar ID de `output/sessions/horizontal_v1_6_session.txt`.
4. Cada `BEGIN` e `END` deve ser confirmado por `[horizontal.v1.6] marked` **antes** de prosseguir. `Request created` não é confirmação da Lua.
5. Em cada intervenção, registrar manualmente se a câmera ficou fixa, se Auto-Aim estava ativo, se havia alvo, se a arma se movimentou e se Bond girou. Marcadores são declarações do operador, não sensores de estado de jogo.

## Intervenções
Compatíveis: `FIXED_NO_TARGET`, `FIXED_AIM_LEFT`, `FIXED_AIM_RIGHT`, `FIXED_AIM_CENTER`, `TURN_LEFT_NO_TARGET`, `TURN_RIGHT_NO_TARGET`, `TURN_LEFT_AIM_OFF`, `TURN_RIGHT_AIM_OFF`, `REST_AFTER_TURN`.

Novas ações: `FIXED_AIM_DISABLED`, `FIXED_AIM_ENABLED`, `FIXED_AIM_WITH_TARGET`, `FIXED_AIM_NO_TARGET`, `NEW_SCENE_BASELINE`. Para controles de ON/OFF, documentar a alteração do ajuste *antes* de BEGIN e não mudar ajuste dentro da janela.

Exemplo:
```powershell
python .\tools\send_horizontal_v1_6.py BEGIN_FIXED_NO_TARGET
# Confirmar no console Lua, observar alguns segundos
python .\tools\send_horizontal_v1_6.py END_FIXED_NO_TARGET
# Confirmar END. Continuar experimentos.
python .\tools\send_horizontal_v1_6.py STOP
# Confirmar FINISHED reason=stop
$session = (Get-Content .\output\sessions\horizontal_v1_6_session.txt -Raw).Trim()
python .\tools\analyze_horizontal_v1_6.py $session
```

## Resultados
- `*_timeline.csv`: todas as oito janelas RAW por amostra, inclusive quando não mudam.
- `*_events.csv`: transições RAW, `*_markers.csv`: intervenção declarada, `*_termination.csv` e `*_discontinuities.csv`: integridade.
- `*_manifest.csv`: domínio, tamanho e origem experimental.
- `*_absolute_audit.csv`: valores iniciais/finais, variação, amplitude, unicidade de RAW e hipótese `float32 BE` por janela e intervenção.
- `*_pair_audit.csv`: sincronização de mudanças, distribuição de `B-A` em **todas as amostras**, direção de variação inicial-final e contagens de desvios de -2 em tolerância 1e-4.

O analisador rejeita intervenções incompletas, ausência de terminação limpa e qualquer descontinuidade; relatórios existentes jamais são sobrescritos. Não executa escrita em memória nem permite Auto-Align/Auto-Shot.

## Estado experimental que motivou a v1.6
Na v1.5.1, os campos `0x0D3998` e `0x0D3D40` variaram em intervalos de mira **e** durante rotação manual de Bond sem alvo. Em 833 eventos simultâneos, interpretação hipotética BE teve `B-A` perto de -2. A v1.6 testa a relação nas **amostras estáveis**, além das transições, e permite contrastar contextos. Nenhuma semântica foi validada.

## Regressão
```powershell
python -m unittest tests.test_horizontal_correction_discovery_v1_6 -v
python -m unittest discover -s tests -v
```
