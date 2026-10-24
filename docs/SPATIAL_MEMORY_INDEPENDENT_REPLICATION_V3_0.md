# Spatial Memory Independent Replication v3.0

Replicação read-only usando uma segunda sessão experimental independente, com o mesmo protocolo da captura `spatial_position_discovery_v2_4.lua`. A janela RDRAM de 80 bytes, as fases e os comandos permanecem idênticos. Endereços D0/E0 são apenas candidatos e controles são blocos escolhidos antes da comparação, não endereços mapeados.

## Nova captura no BizHawk

1. Em outra partida/estado independente, utilize o coletor `spatial_position_discovery_v2_4.lua` já existente. Antes de executar, confirme o domínio `RDRAM` e seu tamanho na interface do BizHawk e preencha `DOMAIN` e `EXPECTED_SIZE` no Lua (como na sessão original); não utilize endereços presumidos. Não reutilize estados/savestates da captura anterior.
2. Inicie o Lua na raiz do repositório e anote o novo identificador impresso: `[spatial.v2.4] session=...`. O novo arquivo `output/sessions/spatial_v2_4_session.txt` será atualizado pelo coletor.
3. Para cada fase, envie exatamente o comando correspondente com `python .\tools\send_spatial_v2_4.py LABEL`; confirme que o Lua imprimiu `marked LABEL` antes de enviar o próximo. Respeite a sequência e mantenha pausas suficientes nas fases de repouso. Sequência: `P0_HOLD`, `FORWARD`, `P1_HOLD`, `BACK`, `P0_RETURN_HOLD`, `ROTATE`, `P0_ROTATED_HOLD`, `FORWARD_AGAIN`, `P2_HOLD`, `STOP`.
4. Após `FINISHED ... reason=stop`, confira que `output/csv/spatial_v2_4_<nova_sessao>_discontinuities.csv` não contém linhas de dados. O analisador rejeita terminação diferente de STOP, ordem incorreta e captura incompleta.

## Validar e comparar

```powershell
git pull --ff-only origin main
python -m unittest tests.test_spatial_replication_v3_0 -v
$original = '20261024T152944Z_311185'
$replica = (Get-Content .\output\sessions\spatial_v2_4_session.txt -Raw).Trim()
python .\tools\analyze_spatial_replication_v3_0.py $original $replica
```

Dois CSVs serão criados sem sobrescrever os anteriores:
- `spatial_v3_0_<original>__<replica>_replication.csv` (9 fases × 4 pares × 2 representações = 72 linhas).
- `spatial_v3_0_<original>__<replica>_control_summary.csv` (4 pares = 4 linhas).

## Consultar
```powershell
Import-Csv ".\output\csv\spatial_v3_0_${original}__${replica}_control_summary.csv" |
 Select-Object pair_type,left,right,mean_test_accuracy_gain_mask,min_test_accuracy_gain_mask,mean_test_logloss_gain_mask,mean_test_sync |
 Format-Table -AutoSize
```

## Método, controles e limites

Para cada fase, treine o modelo condicional **somente na sessão original** e avalie na sessão nova; a linha de base usa apenas frequências da sessão original. Métricas: ganho de acurácia, ganho de log-loss, fração de entradas já observadas, sincronização e phi nos dois conjuntos. Isso impede o vazamento direto de frames de treino/teste, embora ambas as sessões possam compartilhar propriedades ambientais.

Controles negativos predefinidos: blocos `0x3B30B0`×`0x3B30B4`, `0x3B30B8`×`0x3B30BC` e `0x3B30C0`×`0x3B30C4`. São **comparações de referência não verificadas**: podem conter campos correlacionados e não representam garantidamente um controle negativo independente. Não inferir excepcionalidade sem comparar suas métricas e repetir o experimento.

O modelo da v2.9 avalia `change_mask` e `raw_word` em cada fase. `raw_word` pode apresentar generalização ruim ao mudar de sessão. Não concluir validade causal, estrutura comum ou coordenadas somente com sincronização. Nenhuma alteração no `GoldenEye.mapping`.
