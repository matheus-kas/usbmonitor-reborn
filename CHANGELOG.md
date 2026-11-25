# Changelog

Todas as mudanças relevantes do projeto.

## [0.1.0] - 2026-11-24

Primeira versão funcional.

### Adicionado
- Driver serial da tela Turing Smart Screen Rev A (RGB565, 115200 baud).
- Leitura de sensores: CPU, GPU NVIDIA (NVML), RAM, disco, rede por adaptador, uptime, relógio.
- Modelo de tema em JSON com widgets (texto, rótulo, barra, anel, relógio).
- Renderizador com imagem de fundo, transparência e alinhamento de texto.
- Motor de atualização em thread (sensores -> render -> tela).
- 8 temas prontos, incluindo recriações de Gradient, MagicBlue e NZXT a partir das artes originais.
- Interface PySide6: preview ao vivo, galeria visual de temas, controles de brilho,
  orientação, FPS, disco e adaptador de rede.
- Recuperador de retenção de imagem com progresso e cancelamento.
- Bandeja do sistema e opção de iniciar com o Windows.

### Notas
- Teto de banda da tela (~128 KB/s) limita a tela cheia a ~0,4 FPS; vídeo fluido não é suportado.
- Temperatura de CPU no Windows ainda não disponível (depende de integração futura).

## [Não lançado] - pendências

Ver `docs/STATUS.md` e `docs/ROADMAP-SPRINTS.md` para o planejamento completo.

### Em andamento
- Editor visual de temas (base pronta: `Renderer.widget_bbox`).

### Planejado
- Escolher imagem/cor de fundo pela interface e corrigir temas com "%" duplicado na arte.
- Recriar o restante dos temas do fornecedor (~35).
- Temperatura/fan de CPU via LibreHardwareMonitor.
- Tema Claude Code (mascote + uso/limites).
- Widget de clima e novos tipos de widget.
- Reconexão automática, perfis, empacotamento (PyInstaller) e publicação.
