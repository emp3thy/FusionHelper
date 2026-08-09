"""CLI: build the vase and write a slicer-ready 3MF."""

from __future__ import annotations

import argparse
import json
import sys

from fractalvase import DOUADY_HELIX, build_vase
from fractalvase.config import VaseConfig
from fractalvase.validate import MeshInvalid


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fractalvase")
    ap.add_argument("--out", default="douady_helix.3mf", help="output path (.3mf)")
    ap.add_argument(
        "--fast",
        action="store_true",
        help=(
            "coarse grid, for iteration -- the lattice follows the coarser field, so "
            "hole count/euler_number differ from the documented production figures"
        ),
    )
    args = ap.parse_args(argv)

    cfg = VaseConfig(n_theta=96, n_z=80) if args.fast else DOUADY_HELIX
    try:
        mesh, report = build_vase(cfg)
    except MeshInvalid as exc:
        print(f"MESH INVALID: {exc}", file=sys.stderr)
        return 1

    mesh.export(args.out)
    report["output"] = args.out
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
