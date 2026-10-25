# GoldenEye assistant — estado da linha Bond–Soldier v1.8.1

**Versão ativa:** Bond World Landmark Discovery v1.8.1 — Soldier Relative Coordinate Discovery (25/10/2026).

## Recursos implementados
- `tools/analyze_bond_soldier_relative_v1_8_1.py`: auditoria offline, sem modificar RAM, das intervenções EC/F4, controle de Freeze e deslocamentos relativos medidos em um mesmo referencial.
- `tests/test_bond_soldier_relative_v1_8_1.py`: testes de contrato para controle estável, ausência de validação, deriva do soldado e circularidade EC/F4.
- `docs/BOND_SOLDIER_RELATIVE_V1_8_1_TEMPLATE.json`: manifesto inicial propositalmente não validado.
- `docs/BOND_SOLDIER_RELATIVE_DISCOVERY_V1_8_1.md`: execução e limites.
- Reutilização de `docs/ENEMY_COORDINATE_FULL_RAM_V1_8.md` e `docs/FREEZE_ADDRESS_MAPPING_V1_1.md`.

## Dependência canônica
Consultar também `marcosvilhena87/GoldenEye.mapping/experiments/bond_soldier_relative_v1_8_1_20261025.json` antes de interpretar candidatos ou propor endereços. A descoberta de XYZ de inimigo não está validada; `0x02C90C` é indicador experimental de Freeze (não coordenada). `0x0D33EC` e `0x0D33F4` permanecem candidatos de posição de Bond.

## Próxima evidência
1. Um soldado visualmente identificável, estado Freeze ON e OFF comprovado e identidade contínua.
2. Candidato de posição do soldado demonstradamente estável com Freeze ON, com controle de câmera.
3. Posições Bond–Soldado independentemente mensuradas no mesmo quadro de referência.
4. Nova sessão de intervenção isolada EC ou F4, auditada pela v1.6.
5. Executar auditoria v1.8.1, reavaliar sem declarar X/Z canônico.

Nenhum teste realizado no BizHawk é reivindicado neste registro. Os testes Python foram escritos, mas exigem execução local para comprovação.
