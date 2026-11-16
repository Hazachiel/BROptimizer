"""Punto de entrada principal para BROptimizer."""

import sys
from broptimizer.cli import BROptimizerCLI, build_arg_parser
from broptimizer.config import Config, Preset, TargetCategory


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    # Construir configuración a partir de argumentos o valores predeterminados
    config = Config(
        preset=Preset(args.preset),
        target_category=TargetCategory(args.target),
        video_codec=args.video_codec,
        crf=args.crf,
        preserve_extension=not args.no_preserve_ext,
        max_video_workers=args.video_workers,
        max_general_workers=args.threads,
        tag_metadata=not args.no_tag,
        desired_res=args.desired_res,
    )

    app = BROptimizerCLI(config=config)

    if args.folder:
        app.print_banner()
        app.optimize_folder_flow(args.folder)
    else:
        app.run_interactive()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperación interrumpida por el usuario. Saliendo limpiamente...")
        sys.exit(130)
