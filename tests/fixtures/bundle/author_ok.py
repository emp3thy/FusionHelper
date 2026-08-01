"""Minimal valid author script."""
FH_ATTEMPT = 1
FH_OPTS = {"liveness": False}

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import *


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    print("calibration ok, params:", ctx.des.userParameters.count)
