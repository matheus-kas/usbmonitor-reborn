# Roadmap em sprints — UsbMonitor Reborn

Planejamento para evoluir o app até ser 100% personalizável e pronto para publicação.

## Onde estamos (feito)

- Driver da tela Turing Rev A validado no hardware (RGB565, 115200 baud).
- Sensores: CPU, GPU NVIDIA (NVML), RAM, disco, rede por adaptador, uptime, relógio.
- Temas em JSON editável + renderizador (fundo, transparência, alinhamento).
- 8 temas, sendo 3 recriados das artes originais do fornecedor (Gradient, MagicBlue, NZXT).
- Interface PySide6: preview ao vivo, galeria de temas, controles, bandeja, iniciar com Windows.
- Recuperador de retenção de imagem.
- Documentação completa + README profissional + licença GPL-3.0.
- Base do editor iniciada: cálculo da área de cada widget (`Renderer.widget_bbox`).

## Problemas e pedidos em aberto

1. Não dá para escolher imagem de fundo pela interface.
2. Alguns temas do fornecedor têm texto fixo na arte (ex: "%"), e o widget duplica o valor.
3. Não dá para criar/editar dashboards visualmente.
4. Objetivo: app 100% personalizável.
5. Pendentes antigos: tema Claude Code, temperatura de CPU, mais temas do fornecedor.

---

## Sprint 1 — Editor visual de temas (prioridade máxima)

**Status:** planejada. Plano em `docs/sprints/sprint-1-plano.md` (10 passos, critérios A1–A13). Próxima: execução pelo Developer, pelo passo 0 (AGENTS.md e ONDE-PARAMOS.md).

**Objetivo:** criar e editar dashboards na interface, sem mexer em JSON. Resolve os pedidos 1, 2, 3 e 4.

- [ ] Canvas WYSIWYG (QGraphicsView) mostrando o tema renderizado ao vivo.
- [ ] Arrastar e soltar widgets para reposicionar (usa `widget_bbox`).
- [ ] Selecionar imagem de fundo (arquivo) e cor de fundo.
- [ ] Painel de propriedades do widget: tipo, campo de sensor, rótulo, unidade, formato,
      fonte, tamanho, negrito, cor, alinhamento; e cores/limites para barra e anel.
- [ ] Adicionar, remover e duplicar widget.
- [ ] Remover a unidade quando a arte já traz o texto (corrige o "%" duplicado).
- [ ] Salvar, renomear e criar tema novo a partir de um existente.
- [ ] Botões "Novo tema" e "Editar" na galeria da janela principal.

**Entregável:** usuário monta um dashboard do zero e salva, tudo pela interface.

## Sprint 2 — Fundos e biblioteca de temas

**Objetivo:** ampliar o acervo visual e o gerenciamento.

- [ ] Importar imagem de fundo do usuário para `assets/backgrounds/`.
- [ ] Recriar o restante dos temas do fornecedor (~35 arquivos `.data`, imagens já extraídas).
- [ ] Gerenciar temas na galeria: renomear, excluir, duplicar.
- [ ] Miniaturas regeneradas automaticamente ao salvar um tema.

**Entregável:** acervo completo de temas estilo original, com gestão pela interface.

## Sprint 3 — Mais sensores e tipos de widget

**Objetivo:** mais dados e mais formas de mostrá-los.

- [ ] Temperatura e fans de CPU via LibreHardwareMonitor (ponte opcional).
- [ ] Widget de clima por cidade.
- [ ] Novos widgets: gráfico de linha (histórico), ícone/imagem, medidor em arco com escala.
- [ ] Expor campos extras já coletados (RAM em GB, disco em GB, frequência de CPU).

**Entregável:** dashboards mais ricos e informativos.

## Sprint 4 — Tema Claude Code e efeitos

**Objetivo:** itens visuais especiais pedidos.

- [ ] Mascote do Claude Code (desenhado ou imagem fornecida).
- [ ] Widget de uso/limites (definir fonte: métricas locais, entrada manual ou ilustrativo).
- [ ] Plano de fundo com animação leve, dentro do teto de banda da tela.

**Entregável:** tema temático e recursos visuais diferenciados.

## Sprint 5 — Robustez e distribuição

**Objetivo:** deixar pronto para outras pessoas usarem.

- [ ] Reconexão automática quando a tela cai ou o cabo é removido.
- [ ] Perfis: salvar tema + brilho + orientação + FPS juntos e alternar rápido.
- [ ] Empacotar como executável único (PyInstaller) e criar instalador.
- [ ] Testes automatizados do driver, sensores e renderizador.
- [ ] Publicar no GitHub (substituir LICENSE pelo texto oficial, screenshots reais).

**Entregável:** app distribuível e publicado.

## Backlog (sem sprint fixa)

- Player de vídeo/GIF em janela pequena (limitado a ~3 FPS pela banda da tela).
- Temas responsivos que se adaptam à orientação automaticamente.
- Suporte a outras revisões de tela (Rev B, C, D) além da Rev A.
- Integração com AIDA64 (memória compartilhada), como o app original.

## Ordem sugerida

Sprint 1 primeiro, porque entrega o pedido central (personalização total) e já resolve os
temas com texto duplicado. Depois 2 para o acervo visual, 3 para enriquecer, 4 para os
extras e 5 para distribuir.
