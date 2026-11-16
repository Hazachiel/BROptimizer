"""Interfaz de usuario en consola para BROptimizer con Rich."""

import argparse
from pathlib import Path
import sys

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from broptimizer.config import PRESET_DEFINITIONS, Config, Preset, TargetCategory
from broptimizer.engines.base import EngineProfile
from broptimizer.engines.detector import EngineDetector
from broptimizer.logger import LOG_FILENAME
from broptimizer.manager import OptimizationManager, OptimizationSummary
from broptimizer.postprocess import PostProcessor
from broptimizer.rpgmaker_cleaner import RPGMMVCleaner
from broptimizer.scanner import CategoryStats, FileInfo, FolderScanner, MediaStats, MediaType, format_bytes


class BROptimizerCLI:
    """Aplicación de consola orientada a objetos para BROptimizer."""

    def __init__(self, config: Config | None = None) -> None:
        self.console = Console()
        self.config = config or Config()
        self.last_folder: Path | None = None

    def print_banner(self) -> None:
        """Muestra el banner de bienvenida."""
        banner_text = (
            "[bold cyan]BROptimizer[/bold cyan] [green]v1.3.0[/green]\n"
            "[italic white]Optimizador Multimedia Inteligente para Videojuegos y Carpetas[/italic white]\n"
            "[dim]Soporte para Ren'Py, RPG Maker (MZ/MV/XP/VX), Wolf RPG y Carpetas Estándar[/dim]"
        )
        self.console.print(Panel(banner_text, border_style="cyan", box=box.ROUNDED))

    def show_engine_and_stats(self, root_dir: Path, profile: EngineProfile, stats: MediaStats, nwjs_summary: dict | None = None) -> None:
        """Muestra el panel de motor detectado y la tabla de estadísticas previa a la optimización."""
        engine_info = (
            f"[bold]Motor Detectado:[/bold] [yellow]{profile.display_name}[/yellow]\n"
            f"[dim]{profile.description}[/dim]\n"
            f"[bold]Compatibilidad:[/bold] WebP: {'[green]Sí[/green]' if profile.supports_webp else '[red]No (PNG/JPG)[/red]'} | "
            f"Opus: {'[green]Sí[/green]' if profile.supports_opus else '[yellow]No (OGG Vorbis/MP3)[/yellow]'}"
        )
        self.console.print(Panel(engine_info, title="[bold]Análisis del Directorio[/bold]", border_style="blue", box=box.ROUNDED))

        if nwjs_summary and nwjs_summary["count"]:
            self.console.print(
                Panel(
                    f"[cyan]NW.js Redundante Detectado:[/cyan] {nwjs_summary['count']} archivos "
                    f"({format_bytes(nwjs_summary['size'])})",
                    border_style="cyan",
                )
            )

        # Alerta si se detectaron archivos empaquetados o encriptados
        if stats.encrypted_packed_count > 0:
            enc_exts: dict[str, int] = {}
            for f in stats.encrypted_packed_files:
                enc_exts[f.extension.lower()] = enc_exts.get(f.extension.lower(), 0) + 1
            enc_summary = ", ".join(f"{ext} ({cnt})" for ext, cnt in enc_exts.items())

            alert_text = (
                f"[bold magenta]Se detectaron {stats.encrypted_packed_count} archivos multimedia encriptados/empaquetados ({stats.formatted_encrypted_packed_size})[/bold magenta]\n"
                f"[white]Archivos encontrados:[/white] {enc_summary}\n"
                f"[italic dim]* Nota: En futuras versiones se incorporará la opción de desencriptar/desempaquetar estos recursos.[/italic dim]"
            )
            self.console.print(Panel(alert_text, title="[bold magenta]Assets Encriptados / Paquetes Detectados[/bold magenta]", border_style="magenta", box=box.ROUNDED))

        # Tabla de estadísticas
        table = Table(title=f"Contenido de: [bold white]{root_dir.name}[/bold white]", box=box.ROUNDED, expand=True)
        table.add_column("Categoría", style="bold cyan", no_wrap=True)
        table.add_column("Cantidad", justify="right", style="green")
        table.add_column("Peso Total", justify="right", style="yellow")
        table.add_column("Formatos Detectados", style="white")
        table.add_column("Ya Marcados", justify="right", style="dim cyan")

        def format_exts(cat: CategoryStats) -> str:
            if not cat.extensions_count:
                return "[dim]Ninguno[/dim]"
            items = sorted(cat.extensions_count.items(), key=lambda x: x[1], reverse=True)
            return ", ".join(f"{ext} ({cnt})" for ext, cnt in items[:4])

        table.add_row(
            "Imágenes",
            str(stats.images.file_count),
            stats.images.formatted_size,
            format_exts(stats.images),
            str(stats.images.tagged_count),
        )
        table.add_row(
            "Audios",
            str(stats.audios.file_count),
            stats.audios.formatted_size,
            format_exts(stats.audios),
            str(stats.audios.tagged_count),
        )
        table.add_row(
            "Videos",
            str(stats.videos.file_count),
            stats.videos.formatted_size,
            format_exts(stats.videos),
            str(stats.videos.tagged_count),
        )
        table.add_row(
            "Otros (Exe/Scripts/Ini)",
            str(stats.others.file_count),
            stats.others.formatted_size,
            "[dim]Datos del juego[/dim]",
            "-",
        )
        table.add_section()
        table.add_row(
            "[bold white]TOTAL[/bold white]",
            f"[bold white]{stats.total_files}[/bold white]",
            f"[bold green]{stats.formatted_total_size}[/bold green]",
            f"Multimedia: {stats.total_media_count} ({stats.formatted_media_size})",
            f"[bold cyan]{stats.total_tagged_count}[/bold cyan]",
        )

        self.console.print(table)

    def show_settings_panel(self) -> None:
        """Panel interactivo para ver y modificar la configuración."""
        while True:
            self.console.clear()
            self.print_banner()

            table = Table(title="[bold cyan]Panel de Configuración y Presets[/bold cyan]", box=box.ROUNDED, expand=True)
            table.add_column("Opción", style="bold yellow", width=6)
            table.add_column("Parámetro", style="bold white")
            table.add_column("Valor Actual", style="bold green")
            table.add_column("Descripción", style="dim")

            table.add_row(
                "1",
                "Preset de Calidad",
                self.config.preset.value.upper(),
                "Lossy (Mayor compresión) o Nearlossless (Alta fidelidad)",
            )
            table.add_row(
                "2",
                "Objetivo a Optimizar",
                self.config.target_category.value.upper(),
                "Todo (Por etapas), Solo Imágenes, Solo Audio, Solo Video",
            )
            table.add_row(
                "3",
                "Códec de Video",
                self.config.video_codec.upper(),
                "Cicla entre VP8 -> VP9 -> H264",
            )
            table.add_row(
                "4",
                "CRF de Video",
                f"CRF = {self.config.crf}",
                "Cicla entre 15 -> 26 -> 31",
            )
            table.add_row(
                "5",
                "Resolución Deseada Video",
                f"{self.config.desired_res} px",
                "Lado menor (desired_res) para fórmula de bitrate dinámico",
            )
            table.add_row(
                "6",
                "Preservar Extensión Original",
                "[green]ACTIVADO[/green]" if self.config.preserve_extension else "[red]DESACTIVADO[/red]",
                "Mantiene nombres ej. '.png' para imágenes WebP internas",
            )
            table.add_row(
                "7",
                "Límite Conversiones Video",
                f"{self.config.max_video_workers} simultáneo(s)",
                "Evita sobrecalentamiento y saturación (1 o 2 máx)",
            )
            table.add_row(
                "8",
                "Hilos Generales (Img/Audio)",
                f"{self.config.max_general_workers} hilos",
                "Hilos paralelos de procesamiento para medios ligeros",
            )
            table.add_row(
                "9",
                "Marcar Metadata (BROptimized)",
                "[green]ACTIVADO[/green]" if self.config.tag_metadata else "[red]DESACTIVADO[/red]",
                "Incrusta 'BROptimized' para no re-procesar en el futuro",
            )
            table.add_row(
                "10",
                "Ver Detalles Técnicos de Reglas",
                "[cyan]Examinar[/cyan]",
                "Reglas de audio (Vorbis/Opus, 96k cap) y fórmula de video",
            )

            self.console.print(table)
            self.console.print("\n[bold]Escribe el número de la opción a modificar, o [yellow]'0'[/yellow] para volver:[/bold]")
            choice = Prompt.ask("Opción", default="0")

            if choice == "0":
                break
            elif choice == "1":
                self.config.preset = (
                    Preset.NEARLOSSLESS if self.config.preset == Preset.LOSSY else Preset.LOSSY
                )
                self.config.crf = self.config.settings.default_crf
            elif choice == "2":
                cat_choice = Prompt.ask(
                    "Selecciona categoría a optimizar",
                    choices=["all", "images", "audio", "video"],
                    default="all",
                )
                self.config.target_category = TargetCategory(cat_choice)
            elif choice == "3":
                new_codec = self.config.cycle_video_codec()
                self.console.print(f"[green]Códec cambiado a:[/green] [bold yellow]{new_codec.upper()}[/bold yellow]")
            elif choice == "4":
                new_crf = self.config.cycle_crf()
                self.console.print(f"[green]CRF cambiado a:[/green] [bold yellow]{new_crf}[/bold yellow]")
            elif choice == "5":
                res_choice = Prompt.ask("Resolución de video deseada (ej. 480, 600, 720, 1080)", default=str(self.config.desired_res))
                try:
                    self.config.desired_res = max(120, int(res_choice))
                except ValueError:
                    pass
            elif choice == "6":
                self.config.preserve_extension = not self.config.preserve_extension
            elif choice == "7":
                new_val = Prompt.ask("Límite de videos simultáneos (1 o 2)", choices=["1", "2"], default="1")
                self.config.max_video_workers = int(new_val)
            elif choice == "8":
                new_threads = Prompt.ask("Cantidad de hilos generales", default=str(self.config.max_general_workers))
                try:
                    self.config.max_general_workers = max(1, int(new_threads))
                except ValueError:
                    pass
            elif choice == "9":
                self.config.tag_metadata = not self.config.tag_metadata
            elif choice == "10":
                self._show_preset_details()

    def _show_preset_details(self) -> None:
        """Muestra los detalles técnicos de los presets y fórmulas."""
        self.console.clear()
        self.print_banner()

        rules_panel = (
            "[bold cyan]Reglas de Audio (Inspección con FFprobe):[/bold cyan]\n"
            "• [yellow]Códec OGG Predeterminado:[/yellow] Vorbis (o Opus si está especificado).\n"
            "• [yellow]Bitrate Máximo:[/yellow] No superior a 96k. Si el audio original tiene < 96k, se preserva el bitrate original.\n"
            "• [yellow]Sample Rate Opus:[/yellow] No superior a 48k (48000 Hz). Redondea al menor valor aceptable (8k, 12k, 16k, 24k, 48k).\n"
            "• [yellow]Sample Rate Vorbis:[/yellow] Nunca supera 44.1k (44100 Hz).\n\n"
            "[bold cyan]Fórmula Dinámica de Bitrate de Video:[/bold cyan]\n"
            "• aspect_ratio = max(w, h) / min(w, h)\n"
            "• smaller_res = min(desired_res, w, h)\n"
            "• kbps = ((smaller_res ^ 2) * aspect_ratio * fps) / 1000\n"
            "• target_vbit_rate = quality_multiplier * (kbps ^ 0.85)\n"
            "  - Multiplicador H.264: 400 (CRF = 15, 26 o 31)\n"
            "  - Multiplicador VP8/VP9: 250 (CRF = 15, 26 o 31)"
        )
        self.console.print(Panel(rules_panel, title="[bold]Especificaciones Técnicas Avanzadas[/bold]", border_style="cyan", box=box.ROUNDED))
        Prompt.ask("\nPresiona [bold cyan]Enter[/bold cyan] para volver al menú de configuración")

    def optimize_folder_flow(self, folder_str: str | None = None) -> None:
        """Flujo completo de análisis, optimización por etapas y post-procesamiento."""
        if not folder_str:
            if self.last_folder:
                prompt_msg = f"\n[bold cyan]Introduce la ruta de la carpeta o juego (Enter para usar: '{self.last_folder}')[/bold cyan]"
            else:
                prompt_msg = "\n[bold cyan]Introduce la ruta de la carpeta o juego a optimizar[/bold cyan]"

            user_input = Prompt.ask(prompt_msg, default=str(self.last_folder) if self.last_folder else "")
            folder_str = user_input.strip('\'"')
            if not folder_str and self.last_folder:
                folder_path = self.last_folder
            else:
                folder_path = Path(folder_str).resolve()
        else:
            folder_path = Path(folder_str.strip('\'"')).resolve()

        if not folder_path.is_dir():
            self.console.print(f"[bold red]Error:[/bold red] La ruta '{folder_path}' no es un directorio válido.")
            return

        # Recordar la última carpeta válida
        self.last_folder = folder_path

        # 1. Detección de motor
        profile: EngineProfile = EngineDetector.detect(folder_path)

        # 2. Escaneo de archivos
        with self.console.status("[cyan]Escaneando carpeta y analizando metadatos...[/cyan]", spinner="dots"):
            stats = FolderScanner.scan(folder_path, check_tags=True, detect_nwjs=profile.name == "rpgmaker_modern")

        nwjs_summary: dict[str, int | list[Path]] | None = {
            "count": stats.nwjs_count,
            "size": stats.nwjs_size,
            "files": stats.nwjs_files,
        } if profile.name == "rpgmaker_modern" else None

        if stats.total_media_count == 0 and stats.encrypted_packed_count == 0 and not (nwjs_summary and nwjs_summary["count"]):
            self.console.print("[yellow]No se encontraron archivos multimedia compatibles ni paquetes en la carpeta.[/yellow]")
            return

        clean_nwjs = False
        copy_launcher = False
        while True:
            self.console.clear()
            self.print_banner()
            self.show_engine_and_stats(folder_path, profile, stats, nwjs_summary)

            # Selector de acción
            self.console.print("\n[bold cyan]¿Qué deseas optimizar?[/bold cyan]")
            if profile.name == "rpgmaker_modern":
                self.console.print("  [bold yellow][1][/bold yellow] Optimizar Multimedia (Imágenes, Audios, Videos)")
                self.console.print("  [bold yellow][2][/bold yellow] Limpieza de NW.js (archivos redundantes y package.json)")
                self.console.print("  [bold yellow][3][/bold yellow] Optimización Completa (Multimedia + NW.js + Lanzador)")
                self.console.print("  [bold yellow][0][/bold yellow] Volver al menú principal")
                cat_select = Prompt.ask("Opción", choices=["0", "1", "2", "3"], default="1")
                if cat_select == "0":
                    return
                if cat_select == "2":
                    removed, removed_size = RPGMMVCleaner.clean_nwjs(folder_path)
                    patched = RPGMMVCleaner.patch_package_json(folder_path)
                    self.console.print(
                        f"[green]Limpieza completada:[/green] {removed} elementos, "
                        f"{format_bytes(removed_size)} liberados. package.json: "
                        f"{'actualizado' if patched else 'no encontrado/no válido'}."
                    )
                    continue
                clean_nwjs = cat_select == "3"
                copy_launcher = cat_select == "3"
                self.config.target_category = TargetCategory.ALL
            else:
                self.console.print("  [bold yellow][1][/bold yellow] Todo (Por etapas: Imágenes -> Audios -> Videos)")
                self.console.print("  [bold yellow][2][/bold yellow] Solo Imágenes")
                self.console.print("  [bold yellow][3][/bold yellow] Solo Audio")
                self.console.print("  [bold yellow][4][/bold yellow] Solo Video")

                # Opción para desempaquetar / desencriptar si aplica
                has_enc_option = (
                    profile.name in ("renpy", "rpgmaker_modern", "rpgmaker_legacy", "wolfrpg")
                    and stats.encrypted_packed_count > 0
                )
                if has_enc_option:
                    self.console.print(f"  [bold yellow][5][/bold yellow] [magenta]Desempaquetar / Desencriptar recursos ({stats.encrypted_packed_count} archivos) [Próximamente][/magenta]")

                self.console.print("  [bold yellow][0][/bold yellow] Volver al menú principal")

                valid_choices = ["0", "1", "2", "3", "4"]
                if has_enc_option:
                    valid_choices.append("5")

                cat_select = Prompt.ask("Opción", choices=valid_choices, default="1")

                if cat_select == "0":
                    # Volver atrás al menú principal recordando la carpeta
                    return

                if cat_select == "5":
                    self.console.print(
                        f"\n[bold yellow]Funcionalidad en desarrollo:[/bold yellow] La opción de desempaquetar / desencriptar recursos para [cyan]{profile.display_name}[/cyan] "
                        f"estará disponible en una próxima actualización de BROptimizer.\n"
                    )
                    Prompt.ask("Presiona [bold cyan]Enter[/bold cyan] para continuar")
                    continue

                cat_map = {
                    "1": TargetCategory.ALL,
                    "2": TargetCategory.IMAGES,
                    "3": TargetCategory.AUDIO,
                    "4": TargetCategory.VIDEO,
                }
                self.config.target_category = cat_map[cat_select]
            break

        # Confirmación previa con detalles activos
        self.console.print(
            f"\n[bold]Configuración activa:[/bold] Preset=[yellow]{self.config.preset.value.upper()}[/yellow] | "
            f"Objetivo=[green]{self.config.target_category.value.upper()}[/green] | "
            f"Video=[cyan]{self.config.video_codec.upper()} (CRF={self.config.crf})[/cyan] | "
            f"Dimensión más pequeña={f'[cyan]{self.config.desired_res}px[/cyan] | ' if self.config.desired_res > 0 else ''}"
            f"Preservar Extensión={'[green]Sí[/green]' if self.config.preserve_extension else '[red]No[/red]'}"
        )

        if not Confirm.ask("\n¿Deseas iniciar la optimización por etapas?", default=True):
            self.console.print("[yellow]Operación cancelada por el usuario.[/yellow]")
            return

        # Filtrar archivos multimedia según categoría seleccionada
        if self.config.target_category == TargetCategory.IMAGES:
            media_files = [f for f in stats.files if f.media_type == MediaType.IMAGE]
        elif self.config.target_category == TargetCategory.AUDIO:
            media_files = [f for f in stats.files if f.media_type == MediaType.AUDIO]
        elif self.config.target_category == TargetCategory.VIDEO:
            media_files = [f for f in stats.files if f.media_type == MediaType.VIDEO]
        else:
            media_files = [f for f in stats.files if f.media_type != MediaType.OTHER]

        if not media_files:
            self.console.print("[yellow]No hay archivos de la categoría seleccionada para procesar.[/yellow]")
            if profile.name == "rpgmaker_modern" and clean_nwjs:
                self._apply_rpgmaker_actions(folder_path, folder_path, copy_launcher)
            return

        # 3. Procesamiento por etapas secuenciales con barra de progreso
        manager = OptimizationManager(self.config, profile)
        summary: OptimizationSummary | None = None

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console,
        ) as progress:
            task_id = progress.add_task("Iniciando etapas...", total=len(media_files))

            def on_progress(stage_label: str, completed_in_stage: int, total_in_stage: int, file_info: FileInfo, res) -> None:
                short_name = file_info.path.name
                if len(short_name) > 26:
                    short_name = short_name[:23] + "..."
                status_text = "[green]Optimizado[/green]" if (res.is_smaller and not res.skipped) else ("[cyan]Omitido[/cyan]" if res.skipped else "[dim]Sin cambios[/dim]")
                desc = f"[{stage_label}] {short_name} ({status_text})"
                progress.update(task_id, advance=1, description=desc)

            summary = manager.process_files(media_files, progress_callback=on_progress)

        # 4. Mostrar resultados finales
        self.show_summary_results(summary)

        # 5. Opciones de post-procesamiento
        self.handle_postprocess(summary, stats, folder_path, clean_nwjs, copy_launcher)

    def show_summary_results(self, summary: OptimizationSummary) -> None:
        """Muestra el balance final de ahorro y estado de los archivos."""
        self.console.print("\n")
        table = Table(title="[bold green]Resultado Final de la Optimización[/bold green]", box=box.ROUNDED, expand=True)
        table.add_column("Métrica", style="bold cyan")
        table.add_column("Valor", justify="right", style="bold white")

        table.add_row("Tamaño Multimedia Original", summary.formatted_original_size)
        table.add_row("Tamaño Multimedia Optimizado", summary.formatted_optimized_size)
        table.add_row("Espacio Ahorrado", f"[bold green]{summary.formatted_saved_size} ({summary.total_saved_percent:.2f}%)[/bold green]")
        table.add_row("Archivos Reducidos con Éxito", f"[green]{summary.optimized_count}[/green]")
        table.add_row("Archivos Originales Mantenidos (ya óptimos)", f"[yellow]{summary.kept_original_count}[/yellow]")
        table.add_row("Archivos Omitidos (Ya marcados BROptimized)", f"[cyan]{summary.skipped_count}[/cyan]")
        if summary.failed_count > 0:
            table.add_row("Archivos con Errores", f"[red]{summary.failed_count}[/red]")

        self.console.print(table)

        if summary.failed_count > 0:
            self.console.print(
                f"\n[bold red]¡Atención![/bold red] Se registraron {summary.failed_count} fallos durante la conversión.\n"
                f"Consulta el archivo [bold yellow]{LOG_FILENAME}[/bold yellow] para ver el informe técnico y causa de cada error."
            )

    def _apply_rpgmaker_actions(self, source_dir: Path, final_dir: Path, copy_launcher: bool) -> None:
        """Limpia NW.js, actualiza package.json y copia el lanzador si corresponde."""
        removed, removed_size = RPGMMVCleaner.clean_nwjs(final_dir)
        patched = RPGMMVCleaner.patch_package_json(final_dir)
        launcher = Path(__file__).resolve().parent.parent / "nwjs_game_launch.bat"
        copied = RPGMMVCleaner.copy_launcher(final_dir, launcher) if copy_launcher else False
        self.console.print(
            f"[green]NW.js procesado:[/green] {removed} elementos, {format_bytes(removed_size)} liberados; "
            f"package.json {'actualizado' if patched else 'no actualizado'}"
            + (f"; lanzador {'copiado' if copied else 'no copiado'}." if copy_launcher else ".")
        )

    def handle_postprocess(
        self,
        summary: OptimizationSummary,
        stats: MediaStats,
        root_dir: Path,
        clean_nwjs: bool = False,
        copy_launcher: bool = False,
    ) -> None:
        """Presenta las opciones de post-procesamiento requeridas."""
        if summary.optimized_count == 0:
            self.console.print("\n[yellow]No hubo archivos cuyo tamaño pudiera reducirse. No se realizarán cambios.[/yellow]")
            summary.cleanup()
            if clean_nwjs:
                self._apply_rpgmaker_actions(root_dir, root_dir, copy_launcher)
            return

        self.console.print("\n[bold cyan]Selecciona cómo deseas aplicar la optimización:[/bold cyan]")
        self.console.print("  [bold yellow][1][/bold yellow] Reemplazar los archivos originales con los optimizados (In-Place).")
        self.console.print("  [bold yellow][2][/bold yellow] Crear una carpeta nueva y copiar TODOS los archivos faltantes (exe, ini, scripts, dll).")
        self.console.print("  [bold yellow][3][/bold yellow] Cancelar y descartar los archivos optimizados.")

        choice = Prompt.ask("\nOpción", choices=["1", "2", "3"], default="2")

        if choice == "1":
            confirm = Confirm.ask("[bold red]¿Estás seguro de sobrescribir los archivos originales?[/bold red]", default=False)
            if confirm:
                with self.console.status("[yellow]Aplicando optimizaciones in-place...[/yellow]"):
                    count = PostProcessor.apply_in_place(summary, root_dir)
                self.console.print(f"[bold green]¡Listo![/bold green] Se reemplazaron {count} archivos en '{root_dir.name}'.")
                if clean_nwjs:
                    self._apply_rpgmaker_actions(root_dir, root_dir, copy_launcher)
            else:
                self.console.print("[yellow]Operación cancelada. Descartando temporales.[/yellow]")
                summary.cleanup()

        elif choice == "2":
            default_dest = root_dir.parent / f"{root_dir.name}_Optimized"
            dest_input = Prompt.ask(
                "Ruta de la nueva carpeta de destino",
                default=str(default_dest),
            )
            dest_path = Path(dest_input.strip('\'"')).resolve()

            with self.console.status(f"[cyan]Generando carpeta completa en '{dest_path.name}'...[/cyan]"):
                placed, copied = PostProcessor.export_standalone(summary, stats, dest_path, clean_nwjs=clean_nwjs)
                if clean_nwjs:
                    self._apply_rpgmaker_actions(root_dir, dest_path, copy_launcher)

            self.console.print(
                f"\n[bold green]¡Operación completada exitosamente![/bold green]\n"
                f"Carpeta creada: [cyan]{dest_path}[/cyan]\n"
                f"- Archivos optimizados colocados: [green]{placed}[/green]\n"
                f"- Archivos de soporte y faltantes copiados: [yellow]{copied}[/yellow]\n"
                f"[italic]El juego o carpeta está listo para ejecutarse de forma independiente.[/italic]"
            )

        else:
            self.console.print("[yellow]Operación cancelada. Se eliminaron los archivos temporales generados.[/yellow]")
            summary.cleanup()

    def run_interactive(self) -> None:
        """Bucle principal de la interfaz de usuario interactiva."""
        while True:
            self.console.clear()
            self.print_banner()

            self.console.print("\n[bold]Menú Principal:[/bold]")
            self.console.print("  [bold yellow][1][/bold yellow] Optimizar Carpeta / Juego")
            self.console.print("  [bold yellow][2][/bold yellow] Configuración y Presets")
            self.console.print("  [bold yellow][3][/bold yellow] Salir")

            choice = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3"], default="1")

            if choice == "1":
                self.optimize_folder_flow()
                Prompt.ask("\nPresiona [bold cyan]Enter[/bold cyan] para continuar")
            elif choice == "2":
                self.show_settings_panel()
            else:
                self.console.print("[green]¡Hasta luego![/green]")
                sys.exit(0)


def build_arg_parser() -> argparse.ArgumentParser:
    """Configura el parser de argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="BROptimizer - Optimizador multimedia inteligente para juegos y carpetas.")
    parser.add_argument("folder", nargs="?", default=None, help="Ruta de la carpeta a optimizar.")
    parser.add_argument("--preset", choices=["lossy", "nearlossless"], default="lossy", help="Preset de calidad.")
    parser.add_argument("--target", choices=["all", "images", "audio", "video"], default="all", help="Categoría a procesar.")
    parser.add_argument("--video-codec", choices=["vp8", "vp9", "h264"], default="h264", help="Códec de video (h264, vp8, vp9).")
    parser.add_argument("--crf", type=int, choices=[15, 26, 31], default=26, help="CRF de video (15, 26 o 31).")
    parser.add_argument("--desired-res", type=int, default=600, help="Lado mayor de resolución de video deseada.")
    parser.add_argument("--no-preserve-ext", action="store_true", help="No preservar la extensión original del archivo.")
    parser.add_argument("--video-workers", type=int, choices=[1, 2], default=1, help="Límite de conversiones simultáneas de video.")
    parser.add_argument("--threads", type=int, default=None, help="Cantidad de hilos para imágenes y audios.")
    parser.add_argument("--no-tag", action="store_true", help="Desactivar marcado de metadata 'BROptimized'.")
    return parser
