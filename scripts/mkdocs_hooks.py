from pathlib import Path
from mkdocs.structure.files import File

BUILD_DIR = "build"
DEST_PREFIX = "assets/projects"   # where these will appear in your site


def _config_dir(config) -> Path:
    return Path(config.config_file_path).resolve().parent


def on_files(files, config, **kwargs):
    print("on_files")

    root = _config_dir(config)
    build_root = (root / BUILD_DIR).resolve()
    if not build_root.is_dir():
        return files

    # Match: build/<board>/documentation/*
    for doc_dir in build_root.glob("*/documentation"):
        if not doc_dir.is_dir():
            continue

        board = doc_dir.parent.name  # <board-name>

        for src in doc_dir.rglob("*"):
            if not src.is_file():
                continue

            rel_inside = src.relative_to(doc_dir)  # file path inside documentation/
            dest_uri = (Path(DEST_PREFIX) / board / rel_inside).as_posix()

            # Register it as a generated file so MkDocs copies it and serves it.
            files.append(File.generated(config, src_uri=dest_uri, abs_src_path=str(src)))

    return files