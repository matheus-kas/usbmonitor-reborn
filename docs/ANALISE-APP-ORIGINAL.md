# Análise do app original — UsbMonitor.exe (tela USB 3.5")

## Identidade
- .NET Framework 4.0, x86_64, WinForms. Módulo interno: `usb_hid.exe`.
- SHA-256: e2b6ebf6425f397e57fd1eb7beab11888b6c5b6fe0b3bdb3032cefba7ba4b2c0
- 151 tipos, 1186 métodos. Strings criptografadas (BouncyCastle) -> protocolo não sai por análise estática.

## Canal de comunicação com a tela
- Driver em `Driver/usbser` = USB Serial CDC (porta COM virtual). Win10 não precisa instalar driver.
- Resolução: 480x320 (paisagem) / 320x480 (retrato). Painel IPS 3.5".
- `AppConfig` tem: rotation, mirrorMode, invertLcd, blkValue (brilho/backlight), deviceIndex.

## Sensores (fontes de dados)
- NVIDIA via nvml.dll: temp, uso, memória, fan, nome da GPU.
- Disco via disk.dll: GetDiskTemp / InitDiskTemp.
- AIDA64 (opcional): usedAidaCPU, usedAidaGPU, usedAidaHDD (lê memória compartilhada do AIDA64).
- CPU: temp, fan, pump (sub-sensores selecionáveis).
- Rede: netcardName/netcardIndex (throughput).
- Clima: CityName + CityWeatherCode (widget de tempo por cidade).
- Relógio.

## Temas
- Arquivos `config/*.data` = serialização BinaryFormatter do .NET com objetos System.Drawing.
- Guardam imagem de fundo, fontes, cores e posição de cada widget. ~35 temas inclusos.
- `config/statusbar/*.bmp` = gradientes de 108 bytes para barras.
- Renderização via GDI+ (DrawImage, DrawString, DrawArc, DrawPath).

## Config (AppConfig.data, BinaryFormatter)
Campos: CityName, CityWeatherCode, themeIndex, blkValue, noUpdate, invertLcd, rotation,
deviceIndex, mirrorMode, netcardName, netcardIndex, autoRun, barSaveOffset, customColor,
CpuTempSensorSubName, CpuFanSensorSubName, CpuPumpSensorSubName, usedAidaCPU/GPU/HDD,
GpuMemName, GpuName, PartionName, HDDIndex.

## Lacuna para reconstruir
O protocolo serial exato (framing, comandos, formato de pixel: provável RGB565, como envia
o frame 480x320 pela COM) está escondido pelas strings ofuscadas. Recuperar por:
1. Captura em runtime da porta COM enquanto o app original roda (mais confiável), ou
2. Decompilação profunda da rotina de envio (dnSpy/ILSpy após desofuscar).

## O que reaproveitamos desta análise

- **Confirmado o canal serial (usbser/COM virtual)** e a resolução 480x320, base do nosso driver.
- **Mapeados os sensores** (CPU, GPU via NVML, disco, rede, uptime, clima, relógio) que
  replicamos em `core/sensors.py`.
- **Formato dos temas** entendido (BinaryFormatter com imagens embutidas): extraímos as artes
  de fundo (Gradient, MagicBlue, NZXT) e as recriamos em JSON.
- **Ferramenta usada:** REA (análise do assembly .NET).

## Pendências ligadas ao original

- Strings ofuscadas (BouncyCastle) não foram decifradas; não foi necessário, pois o protocolo
  já era conhecido pela comunidade.
- Recriar o restante dos ~35 temas do fornecedor.
- Opcional: integração com AIDA64 por memória compartilhada, como o app original faz.
