# BROptimizer 🚀

**BROptimizer** es una aplicación Python con interfaz gráfica PySide6 y CLI, orientada a reducir drásticamente el peso de archivos multimedia (imágenes, audios y videos) manteniendo una calidad perceptualmente idéntica al original humano.

Especialmente adaptada para optimizar recursos en videojuegos de **Ren'Py**, **RPG Maker** (MZ, MV, XP, VX, VX Ace), **Wolf RPG Editor**, y carpetas estándar de assets.

\---

## ✨ Características Principales

1. **Códecs y Valores Predeterminados**:

   * **Video**: `H.264` como códec predeterminado con **CRF = 26** (alta compatibilidad y fidelidad).
   * **Audio**: `Vorbis` como códec predeterminado para archivos OGG/WAV.
2. **Ciclos de Configuración Interactivos**:

   * Códec de video cicla con un solo toque: `VP8` $\\rightarrow$ `VP9` $\\rightarrow$ `H264` $\\rightarrow$ `VP8`.
   * CRF cicla con un solo toque: `15` $\\rightarrow$ `26` $\\rightarrow$ `31` $\\rightarrow$ `15`.
3. **Soporte Robusto y Corregido para H.264**:

   * Solución a errores de compatibilidad: aplica formato de píxeles universal `-pix\_fmt yuv420p`, corrección a dimensiones pares (`target\_res = round(res / 2) \* 2`) y forzado de muxer Matroska (`-f matroska`) cuando se preserva la extensión `.webm`.
4. **Navegación con Memoria de Última Ruta**:

   * Desde el menú de selección de objetivo es posible volver atrás con la opción `\[0]`.
   * El programa recuerda la última ruta analizada y permite seleccionarla rápidamente pulsando simplemente `Enter`.
5. **Placeholder para Desempaquetado y Desencriptado**:

   * Si se detectan assets protegidos en juegos de Ren'Py, RPG Maker o Wolf RPG, se habilita la opción `\[5]` con un aviso informativo sobre su próxima disponibilidad.
6. **Sistema de Registro de Errores Detallado (`broptimizer\_errors.log`)**:

   * Cualquier excepción de Python o fallo de FFmpeg/Pillow genera una entrada estructurada indicando timestamp, módulo/bloque de código, archivo afectado y el mensaje o traza completa de error.
7. **Conversión Secuencial por Etapas y Filtro de Medios**:

   * Procesamiento ordenado por fases: **1° Imágenes** $\\rightarrow$ **2° Audios** $\\rightarrow$ **3° Videos**.
   * Selector interactivo y por argumentos para elegir: **Todo**, **Solo Imágenes**, **Solo Audio**, o **Solo Video**.
8. **Detección de Archivos Encriptados y Empaquetados**:

   * Identifica assets protegidos: `.rpgmvp`, `.rpgmvm`, `.rpgmvo`, `.png\_`, `.ogg\_`, `.m4a\_`, `.rgssad`, `.rgss2a`, `.rgss3a`, `.rpa`, `.wolf`.
9. **Reglas Inteligentes de Audio con FFprobe**:

   * Límite de bitrate a un máximo de **96 kbps** (preservando bitrates menores si el archivo original ya era inferior).
   * Sample rate de **Opus $\\le$ 48k** y **Vorbis $\\le$ 44.1k**.
10. **Fórmula Dinámica de Video con FFprobe**:

    * Cálculo de bitrate ajustado en base a resolución objetivo (`target\_res`, por defecto = desired\_res = 600) y multiplicador de calidad (400 para H.264, 250 para VP8/VP9).
11. **Preservación de Extensión y Regla de Oro de Descarte**:

    * Opción de mantener extensiones originales (`.png` para WebP interno).
    * Descarte automático de archivos procesados que no logren reducir el peso original.
12. **Opciones Post-Procesamiento**:

    * **Opción 1 (In-Place)**: Reemplaza en la carpeta original.
    * **Opción 2 (Clonación Standalone)**: Genera una carpeta nueva y copia automáticamente todos los archivos faltantes (`.exe`, `.ini`, `.dll`, scripts).
13. **Interfaz gráfica PySide6**:
* Análisis visual por pestañas, configuración avanzada y progreso sin bloquear la ventana.
* Limpieza de NW.js para RPG Maker MV/MZ y exportación de copias optimizadas.

\---

## 📋 Requisitos e Instalación

* **Python 3.10+** (probado en Python 3.14)
* **FFmpeg y FFprobe** en el PATH del sistema
* Librerías:

```bash
  pip install -r requirements.txt
  ```

\---

## 🚀 Guía de Uso

### Modo Interactivo

```bash
python main.py
```

Desde el menú interactivo podrás seleccionar qué optimizar, alternar cíclicamente códecs y CRF en el panel de configuración, y volver atrás en cualquier momento conservando la ruta en memoria.

### Interfaz gráfica

```bash
python gui\_main.py
```

La GUI ofrece navegación lateral para Inicio, Análisis, Optimización, Resultados y Configuración. Las operaciones de análisis y conversión se ejecutan en segundo plano para mantener la ventana responsiva. La opción **Optimización completa** incluye la limpieza NW.js y la copia de `nwjs\_game\_launch.bat` en el destino final.

### Modo por Línea de Comandos

```bash
# Optimizar con defaults (H.264, CRF 26, Vorbis)
python main.py "C:\\Ruta\\Al\\Juego"

# Optimizar usando H.264 con CRF 26
python main.py "C:\\Ruta\\Al\\Juego" --video-codec h264 --crf 26

# Optimizar solo imágenes
python main.py "C:\\Ruta\\Al\\Juego" --target images
```

Opciones disponibles:

* `folder`: Ruta de la carpeta a procesar.
* `--target {all, images, audio, video}`: Categoría a procesar.
* `--video-codec {vp8, vp9, h264}`: Códec de video (por defecto `h264`).
* `--crf {15, 26, 31}`: Nivel CRF (por defecto `26`).
* `--desired-res N`: Lado menor para la fórmula de video (por defecto `600`).
* `--no-preserve-ext`: Aplica extensión nativa del formato convertido.
* `--video-workers {1, 2}`: Límite de videos simultáneos.
* `--threads N`: Número de hilos para imágenes y audios.
* `--no-tag`: Desactiva la marca de metadata `BROptimized`.

\---

## 🧪 Pruebas Automatizadas

```bash
python -m unittest discover tests
```

