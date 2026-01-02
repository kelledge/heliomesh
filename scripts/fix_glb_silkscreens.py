#!/usr/bin/env python3
import argparse
import os
import tempfile
from pygltflib import GLTF2


def looks_like_silkscreen(mat, white_thresh: float, min_alpha: float) -> bool:
    """
    Heuristic for KiCad silkscreen:
      - alphaMode == BLEND
      - baseColorFactor is near-white
      - alpha is fairly high (ink, not glass)
    """
    if mat is None:
        return False

    if getattr(mat, "alphaMode", None) != "BLEND":
        return False

    pbr = getattr(mat, "pbrMetallicRoughness", None)
    if not pbr or not getattr(pbr, "baseColorFactor", None):
        return False

    bc = pbr.baseColorFactor
    if len(bc) != 4:
        return False

    r, g, b, a = bc
    if a < min_alpha:
        return False

    return (r >= white_thresh) and (g >= white_thresh) and (b >= white_thresh)


def make_opaque(mat) -> None:
    pbr = mat.pbrMetallicRoughness
    if pbr and pbr.baseColorFactor and len(pbr.baseColorFactor) == 4:
        pbr.baseColorFactor[3] = 1.0  # alpha=1

    mat.alphaMode = "OPAQUE"
    mat.alphaCutoff = None
    mat.doubleSided = True


def main():
    ap = argparse.ArgumentParser(
        description="Force KiCad silkscreen-like BLEND materials to OPAQUE (fixes WebGL angle artifacts)."
    )

    ap.add_argument("in_glb", help="Input .glb file")
    ap.add_argument(
        "out_glb",
        nargs="?",
        default=None,
        help="Output .glb file (omit when using --inplace)",
    )
    ap.add_argument(
        "--inplace",
        action="store_true",
        help="Modify the input file in-place (writes via temp file + atomic replace).",
    )

    ap.add_argument("--white-thresh", type=float, default=0.95,
                    help="RGB threshold for 'near-white' (default 0.95)")
    ap.add_argument("--min-alpha", type=float, default=0.7,
                    help="Minimum alpha to treat as silkscreen ink (default 0.7)")
    ap.add_argument("--name-hint", action="append", default=[],
                    help="Optional material-name hint(s) (case-insensitive). If provided, name match OR heuristic match will select. "
                         "Example: --name-hint silk --name-hint screen")
    ap.add_argument("--dry-run", action="store_true", help="Print what would change, but do not write output.")
    args = ap.parse_args()

    if args.inplace and args.out_glb is not None:
        ap.error("Provide either OUT_GLB or --inplace, not both.")

    if not args.inplace and args.out_glb is None:
        ap.error("You must provide OUT_GLB unless using --inplace.")

    gltf = GLTF2().load(args.in_glb)

    hints = [h.lower() for h in args.name_hint]
    chosen = []

    for i, m in enumerate(gltf.materials or []):
        name = (m.name or "").lower()

        name_match = False
        if hints:
            name_match = any(h in name for h in hints)

        heuristic_match = looks_like_silkscreen(m, args.white_thresh, args.min_alpha)

        if name_match or heuristic_match:
            chosen.append(i)
            if not args.dry_run:
                make_opaque(m)

    if not chosen:
        print("No silkscreen-like materials matched.")
        print("Tip: lower --white-thresh (e.g. 0.9) or --min-alpha, or add --name-hint.")
    else:
        print(f"Matched materials: {chosen}")
        for mid in chosen:
            m = gltf.materials[mid]
            bc = getattr(getattr(m, "pbrMetallicRoughness", None), "baseColorFactor", None)
            print(f"  {mid}: name={m.name!r} alphaMode={m.alphaMode!r} baseColorFactor={bc}")

    if args.dry_run:
        print("Dry-run: no file written.")
        return

    if args.inplace:
        in_path = os.path.abspath(args.in_glb)
        in_dir = os.path.dirname(in_path) or "."
        base = os.path.basename(in_path)

        # 1. Create a named temp file in the same directory
        # delete=False is required so the file stays on disk after we close it
        tmp = tempfile.NamedTemporaryFile(
            prefix=base + ".", suffix=".glb", dir=in_dir, delete=False
        )
        tmp_path = tmp.name
        
        try:
            # 2. Close the handle IMMEDIATELY. 
            # We only wanted the unique 'tmp_path'.
            tmp.close()
            
            # 3. Let pygltflib handle the opening/writing to this path
            gltf.save_binary(tmp_path)
            
            # 4. Set permissions to 0o644 (rw-r--r--) before the move
            os.chmod(tmp_path, 0o644)
            
            # 5. Atomic swap
            os.replace(tmp_path, in_path)
            
        except Exception as e:
            # Clean up the temp file if anything failed before the replace
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise e
        print(f"Wrote in-place: {in_path}")
    else:
        gltf.save_binary(args.out_glb)
        print(f"Wrote: {args.out_glb}")


if __name__ == "__main__":
    main()