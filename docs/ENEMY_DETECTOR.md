# Enemy Detector v0.1 — contrato observacional

O módulo `lua/enemies.lua` recebe **observações externas**, sem descobrir ou ler endereços de RAM. Ele **não** controla botões, mira ou disparos.

## Interface

`local detector = dofile("lua/enemies.lua").new(memory_api)`

`local report, err = detector:update(observation)`

A observação deve conter `complete=true`, `source="validated_mapping"`, `rom_id` e `mapping_commit` não vazios, e `entities` como array denso. Cada entidade deve ter `id` textual exclusivo e `classification_status="validated"`, `hostile` e `alive` booleanos para ser classificada. Ausências são colocadas em `unknown`.

O resultado contém `enemies` (IDs hostis vivos), `unknown`, contagens e `observational_only=true`. A lista não equivale a alvos visíveis ou alcançáveis.

**Limite crítico:** os campos de origem são declarações recebidas, não autenticação criptográfica. Até existir um adaptador auditado que verifique ROM em execução, commit, domínio e condições dos símbolos canônicos, a saída só é apropriada para testes com fixtures. Não conectar a auto-shot ou tratar os IDs das fixtures como fatos sobre a ROM.

## Teste sem jogo

`lua tests/enemy_detector_smoke.lua`

## Próxima fase

Mapear experimentalmente a enumeração de entidades, identidade, hostilidade e vida no `GoldenEye.mapping`; validar proveniência no adaptador BizHawk antes de qualquer leitura em runtime.
