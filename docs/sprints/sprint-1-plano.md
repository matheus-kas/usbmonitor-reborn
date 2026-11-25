# Sprint 1 — Editor visual de temas: plano de implementação

Status: **planejado, aguardando Developer**. Nenhum código foi escrito nesta etapa.
Base: `docs/ROADMAP-SPRINTS.md` (Sprint 1), `docs/STATUS.md`, `docs/ARQUITETURA.md`.

## 1. Objetivo

Criar e editar dashboards pela interface, sem mexer em JSON. Resolve os pedidos 1 (imagem de
fundo pela UI), 2 (temas com "%" duplicado), 3 (criar/editar dashboards) e 4 (app personalizável).

**Entregável:** o usuário monta um dashboard do zero, ajusta, salva e aplica na tela, tudo pela UI.

## 2. Estado de partida (verificado no código)

- `core/theme.py`: `Theme` e `Widget` (dataclasses) com `to_dict/from_dict/save/load`. Tipos:
  `text`, `label`, `clock`, `bar`, `ring`. Campos de posição: `x`, `y`; `unit` é sufixo de texto.
- `core/renderer.py`: `Renderer.render(reading)` gera a imagem PIL; `Renderer.widget_bbox(w, reading)`
  já devolve a área de cada widget (base do editor).
- `core/theme_store.py`: `list_themes()` lê `themes/*.json` e ignora arquivo inválido em silêncio;
  `load_theme(name)` procura **pelo nome do arquivo** (`{name}.json`), não pelo campo `name`.
- `ui/main_window.py`: galeria, preview, controles; botão "Recuperar retenção" já existe.
- `core/engine.py`: a UI só ajusta parâmetros do motor (tema, brilho, orientação, FPS). Não escreve na serial.
- Não existe suíte de testes automatizados, nem pasta `tests/`, nem `pytest` no `requirements.txt`.
  `teste_tela.py` e `run_headless.py` são scripts manuais.
- Não existe `.git` no projeto (ver pergunta 1).
- Python da venv: 3.12.10 (`.venv/pyvenv.cfg`).

## 3. Decisões de arquitetura (tomadas pelo Planner)

1. **Sem mudar o formato do JSON.** O "%" duplicado é resolvido zerando `unit` nos temas afetados
   e com o painel de propriedades, que deixa o campo `unit` vazio. Não cria campo novo.
2. **Canvas:** `QGraphicsView` mostra o quadro já renderizado por `Renderer.render` (fundo + widgets).
   Sobre ele ficam retângulos de seleção, desenhados com `widget_bbox`. Arrastar altera `x`/`y`
   do `Widget` e pede re-render. Não se desenha widget por widget no Qt: a fonte de verdade é o Pillow.
3. **Imagem de fundo:** o seletor de arquivo **copia** a imagem para `assets/backgrounds/` e grava o
   caminho relativo em `background_image`. Isso puxa um item da Sprint 2 para cá, porque caminho
   absoluto quebra o tema em outro computador. `Renderer._resolve_bg` já aceita caminho relativo.
4. **Cor de fundo:** usa `background_color` já existente, com seletor de cor.
5. **Propriedades:** o painel lista só os campos de `Widget`. O campo de sensor (`field`) vem de uma
   lista fixa dos campos de `Reading` (o Developer confirma a lista em `core/sensors.py`).
6. **Salvar/renomear/novo:** a regra é uma só: **nome do tema = nome do arquivo**. Renomear troca os
   dois juntos. Isso evita o defeito de `load_theme`, que procura pelo arquivo e não pelo campo `name`.
7. **Escrita em disco** só pelo `Theme.save`, em `themes/`, feita pela UI. Nenhum teste escreve em
   `themes/` real (ver seção 5).
8. **Fora do caminho da serial:** o editor só altera o `Theme` em memória e manda para o motor por
   `set_theme`. Não há acesso à porta serial a partir do editor.
9. **Testes automatizados entram já nesta sprint, mínimos** (ver pergunta 2). Dependência só de
   desenvolvimento: `requirements-dev.txt` com `pytest`. `requirements.txt` não muda.

## 4. Ordem de execução

Cada passo termina com o critério de aceite correspondente antes do próximo.

| # | Passo | Entrega | Prova de pronto |
|---|---|---|---|
| 0 | Pré-requisitos de documentação e git (seção 7) | `AGENTS.md`, `docs/ONDE-PARAMOS.md`, repo git (se aprovado) | arquivos existem; `git status` mostra o baseline |
| 1 | Testes de base do modelo e do store | `tests/test_theme.py`, `tests/test_theme_store.py` | `pytest` verde antes de mexer em UI |
| 2 | Operações puras de edição (sem UI): mover, adicionar, remover, duplicar widget; criar, renomear, salvar tema | funções em `core/` (módulo novo, ex.: `core/editor.py`) | testes unitários de cada operação |
| 3 | Canvas `QGraphicsView` com preview ao vivo e seleção | `ui/editor.py` | teste de que a área de seleção bate com `widget_bbox`; checagem visual na tela real |
| 4 | Arrastar e soltar widget | evento de mouse no canvas chama operação do passo 2 | teste: `x`/`y` mudam e o JSON salvo reflete a posição |
| 5 | Painel de propriedades | campos do `Widget` editáveis; sem campo, formato inválido é recusado com mensagem | teste: valor inválido não altera o tema |
| 6 | Imagem e cor de fundo | seletor copia imagem para `assets/backgrounds/`; seletor de cor | teste: arquivo copiado existe e `background_image` é relativo |
| 7 | Botões "Novo tema" e "Editar" na galeria | integração com `ui/main_window.py` | teste de abertura do editor com tema existente |
| 8 | Remover unidade duplicada nos temas do fornecedor | `unit` zerado nos temas com "%" já na arte | verificação visual no preview de cada tema afetado; diff do JSON mostra só `unit` |
| 9 | Verificação de regressão e sprint fechada | suíte completa 2x seguidas; app abre; tema existente carrega; tela real aplica tema editado | ver seção 6 |

## 5. Critérios de aceite (verificáveis)

Cada item tem a prova que o Tester roda. "Visual" = conferido por humano na tela real.

| # | Critério | Prova |
|---|---|---|
| A1 | Editor abre com um tema da galeria e mostra o quadro renderizado | teste de integração (offscreen) + visual |
| A2 | Seleção de widget desenha a área de `widget_bbox` | teste comparando retângulo com `widget_bbox` |
| A3 | Arrastar muda `x`/`y` e o quadro re-renderiza | teste unitário da operação + teste de re-render |
| A4 | Adicionar, remover e duplicar widget preservam os demais | teste unitário (contagem e ordem) |
| A5 | Propriedade inválida (ex.: `size` negativo ou fonte vazia) é recusada | teste unitário |
| A6 | Salvar grava JSON que `Theme.load` lê de volta sem perda | teste de round-trip |
| A7 | Renomear troca nome e arquivo; `load_theme(novo_nome)` funciona | teste de store |
| A8 | Nome duplicado é recusado (não sobrescreve outro tema) | teste de store |
| A9 | Imagem de fundo é copiada para `assets/backgrounds/` e o caminho gravado é relativo | teste de store/editor |
| A10 | Tema com "%" corrigido não mostra "%" duplicado | visual no preview |
| A11 | Testes **não escrevem em `themes/` nem em `assets/` reais** | teste usa diretório temporário (`tmp_path` + `monkeypatch` em `THEMES_DIR`); conferido por `git status`/listagem antes e depois |
| A12 | Nenhum arquivo do driver (`driver/`) foi alterado | `git diff --stat` mostra só `core/`, `ui/`, `themes/`, `tests/`, `docs/`, `assets/` |
| A13 | Tema editado aparece na tela real | visual, com o hardware conectado |

## 6. Como o Tester prova que está pronto

1. `pytest` na venv `.venv` (Python 3.12), **rodado 2 vezes seguidas** sem limpar o ambiente.
2. Conferir que a listagem de `themes/` e `assets/backgrounds/` não mudou depois da suíte (A11).
3. Abrir o app, editar um tema, salvar, reabrir: o tema tem as mudanças.
4. Aplicar o tema editado na tela real e conferir visualmente (A13).
5. Se algum teste falhar: achar a causa antes de concluir. Não supor "é flaky" nem "é regressão" sem prova.

## 7. Pré-requisitos e ajustes de documentação

**Documentação (Documenter, antes do Developer):**
- Criar `AGENTS.md` na raiz com o contrato do pipeline (modelo do método, seção "Anexo").
  Regra não negociável deste projeto: **nunca alterar `themes/` real a partir de teste**.
- Criar `docs/ONDE-PARAMOS.md` (reescrito no topo a cada sessão).
- Sincronizar `docs/STATUS.md` com o roadmap. Hoje a seção "Pendências" está **incompleta**:
  - faltam: testes automatizados (Sprint 5), gerenciar temas (renomear/excluir/duplicar),
    miniaturas automáticas, expor campos extras (RAM/disco em GB, frequência), gráfico/ícone,
    plano de fundo animado, perfis como item próprio;
  - a ordem está diferente do roadmap. O roadmap manda: Sprint 1 (editor + "%"), 2 (fundos e
    acervo), 3 (sensores e widgets), 4 (Claude Code e efeitos), 5 (robustez e distribuição).
  - Sugestão: a lista do STATUS passa a ser "Sprint 1 … Sprint 5 + backlog", igual ao roadmap, sem
    duplicar o texto. O STATUS continua histórico e não é reescrito.

**Git (Developer, depois da aprovação):**
- Sem `.git`, não há como cumprir "confirmar `git log`" nem "revisar `git diff --stat`". Ver pergunta 1.

**Stack:**
- Nenhuma tecnologia nova além de `pytest` (dev). Nada de banco, nada de rede.

## 8. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| `load_theme` busca por nome de arquivo, `list_themes` lista pelo campo `name` | Tema renomeado some ao abrir | Regra da seção 3.6 + teste A7 |
| `Widget(**w)` quebra com chave desconhecida | Tema salvo pelo editor com campo novo não carrega | Editor só grava campos que o `Widget` já tem; teste de round-trip A6 |
| `list_themes` ignora JSON inválido em silêncio | Tema "sumido" sem aviso | Editor mostra erro ao salvar; decidir se `list_themes` loga o erro (fora do escopo, anotar) |
| Teste ou editor escreve em `themes/` real | Perda de tema do usuário | `THEMES_DIR` redirecionado em teste (A11); conferência antes/depois |
| `THEMES_DIR.mkdir()` roda na importação de `theme_store` | Efeito colateral ao importar | Aceito nesta sprint; não mexer, só anotar |
| Render a cada arrasto no canvas | Preview travado | Re-render só ao soltar o mouse, não a cada pixel (Developer valida) |
| Tela real tem teto de ~0,4 FPS em quadro cheio | Preview do app ≠ tela | Preview é só visual; tela recebe o frame quando o motor manda |
| Escopo grande (9 itens do roadmap) | Sprint estourar | Ordem da seção 4 com checkpoints; se atrasar, o Developer para no passo 7 e avisa o Planner |

## 9. Fora de escopo desta sprint

- Desfazer/refazer (undo/redo).
- Gerenciar temas (excluir, duplicar na galeria) e miniaturas automáticas: Sprint 2.
- Importar fundo para `assets/backgrounds/` como tela separada: já coberto pelo passo 6, mas a tela de
  biblioteca é Sprint 2.
- Gráfico de linha, ícone, medidor em arco com escala: Sprint 3.
- Temperatura de CPU, LibreHardwareMonitor: Sprint 3.
- Reconexão automática, perfis, PyInstaller, LICENSE: Sprint 5.
- Qualquer alteração em `driver/turing_screen.py` e em `core/engine.py` (só leitura para o editor).
- Mudanças de formato de JSON.

## 10. Perguntas ao usuário

1. **Git:** o projeto `usbmonitor-reborn` não é repositório git. Posso fazer `git init` (sem commit)
   antes do Developer começar? **Recomendação: sim.** Sem isso, a disciplina de git do método não
   tem como ser cumprida. O commit fica para depois da sua aprovação.
2. **Testes na Sprint 1:** o roadmap deixa testes automatizados para a Sprint 5. Eu recomendo
   adiantar **só o mínimo** (modelo, store e operações do editor) nesta sprint, para o editor não
   ser escrito sem rede de segurança. **Recomendação: sim, testes mínimos agora; suíte completa na Sprint 5.**
   Se preferir só na Sprint 5, o passo 1 some e o critério A11 vira verificação manual.

Os dois itens acima têm padrão definido: se o usuário não responder, o Developer segue com a
recomendação, mas não faz `git init` antes da resposta à pergunta 1.

## 11. Resumo para o Developer

- Comece pelo passo 0 (documentação) e pelo passo 1 (testes de base), antes de qualquer UI.
- Não altere `driver/`. Não escreva em `themes/` ou `assets/` a partir de teste.
- Não faça commit: entregue o diff e avise o Reviewer.
- Se precisar mudar o escopo no meio (ex.: exigir mudança de formato de JSON), volte ao Planner.
