# Manual Controls Recognition v2.2.1 — Session Safety

Conserva testes independentes (v2.2) e usa exclusivamente os controles do perfil exportado de `GoldenEye.mapping`. Não escreve na RAM nem injeta comandos de controle.

## Inicializar
- Encerre o detector anterior e atualize `GoldenEye.assistant`.
- Mantenha `config/manual_controls_default.lua` sincronizado com o mapping.
- Inicie `manual_controls_v2_2_1.lua` na Lua Console (diretório de trabalho: raiz do assistente).
- O detector cria `manual_controls_v2_2_1_session.txt` com identificador único e uma fila dedicada àquela sessão.

## Operação

```powershell
python .\tools\send_controls_v221.py PHASE gameplay
```

Pressione Z, R, A, B; depois consulte as pendências:

```powershell
python .\tools\send_controls_v221.py LIST all
```

Para validar a última pressão de Z, após confirmar visualmente o disparo:

```powershell
python .\tools\send_controls_v221.py OBSERVED Z latest fire_manual
python .\tools\send_controls_v221.py RESULT Z latest yes
```

Outros comandos: `OBSERVED R latest visual_aim`, `OBSERVED A latest cycle_weapon`, `OBSERVED B latest reload`; para cada observação, finalize com `RESULT BOTAO latest yes` quando comprovada. Para testar uma ocorrência mais antiga, substitua `latest` pelo `trial_id` exato exibido no LIST. Execute `RESULT no` ou `RESULT unknown` quando apropriado.

## Proteções
- O emissor confere se o ID ainda está pendente **na sessão ativa** e pertence ao botão especificado.
- O detector verifica novamente sessão, ID e botão, protegendo contra relatórios defasados.
- Comandos antigos ficam em subpastas de sessão diferentes e não serão consumidos após reiniciar.
- `phase` é alterada apenas pelo comando `PHASE`, que precisa ser enviado antes de realizar os testes.
- Filas devem ter um emissor por vez. Se um comando for rejeitado por corrida, veja diagnostics e faça novamente após verificar o estado.
- Relatório `_pending.csv` contém somente os testes abertos da sessão atual.
- `operator_observed` significa confirmação declarada pelo operador, não leitura automatizada do efeito no jogo.

Relatórios: `_events.csv`, `_annotations.csv`, `_validation.csv`, `_diagnostics.csv`, `_pending.csv`; todos começam com `manual_controls_v2_2_1`.
