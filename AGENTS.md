# AGENTS.md — UsbMonitor Reborn

> Contrato que todo agente (IA) ou pessoa le antes de mexer neste repositorio.
> Pipeline: **Planejar -> Desenvolver -> Revisar -> Testar -> (se tudo passar) Documentar.**
> Nenhuma etapa e pulada, mesmo em tarefas pequenas.

## Contexto obrigatorio antes de qualquer tarefa

- Este arquivo
- `docs/ARQUITETURA.md` — estrutura de pastas e decisoes de design
- `docs/STATUS.md` — o que ja foi feito e as pendencias
- `docs/ONDE-PARAMOS.md` — ponto de retomada rapido (reescrito no topo a cada sessao)
- `docs/ROADMAP-SPRINTS.md` e o plano da sprint em `docs/sprints/sprint-N-plano.md`

## Regras nao-negociaveis

1. **Nunca alterar `themes/` ou `assets/` reais a partir de teste.** Testes usam diretorio
   temporario (`tmp_path` + `monkeypatch`). Conferir a listagem antes e depois da suite.
2. **Nunca tocar a tela real, a porta serial, o registro do Windows ou APIs externas em teste.**
   Serial, NVML, psutil e winreg sao simulados. O `driver/` so muda com plano que peca isso.
3. **Nenhum segredo no repositorio.** Nao ler `.env` nem credenciais.
4. **Formato do JSON de tema nao muda sem passar pelo Planner.**
5. **Nome do tema = nome do arquivo** (`themes/<nome>.json`). Renomear troca os dois juntos.

## Agentes do pipeline

- **planner**: escreve `docs/sprints/sprint-N-plano.md` com criterios de aceite. Nao escreve codigo.
- **developer**: implementa exatamente o plano, com testes. Se o escopo mudar, volta ao planner.
  Roda a suite 2 vezes seguidas antes de cada commit. Nao faz merge na main nem force-push.
- **reviewer**: confere plano, regras acima, seguranca e qualidade. Reprova de volta ao developer.
- **tester**: roda a suite inteira 2 vezes seguidas, em ambiente descartavel. Investiga a causa
  raiz de qualquer falha.
- **documenter**: so depois de reviewer e tester aprovarem. Gera `docs/sprints/sprint-N-entregue.md`
  e atualiza `STATUS.md` e `ONDE-PARAMOS.md`.

```
planner -> developer -> reviewer -+-(reprovado)-> developer
                                  +-(aprovado)-> tester -+-(falhou)-> developer
                                                         +-(passou)-> documenter
```

## Git e testes

- Commits pequenos, em portugues, sem mencao a IA. Revisar `git diff --stat` antes de commitar.
- Confirmar com `git log` que o commit existe. Branch por sprint: `sprint-N/<slug>`.
- Rodar testes: `.venv\Scripts\python.exe -m pytest` (dependencia de dev: `requirements-dev.txt`).
