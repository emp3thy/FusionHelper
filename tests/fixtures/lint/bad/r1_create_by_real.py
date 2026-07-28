import adsk.core


def run(_context: str):
    v = adsk.core.ValueInput.createByReal(0.6)  # EXPECT: R1
    vi = adsk.core.ValueInput
    w = vi.createByReal(1.0)  # EXPECT: R1
    print(v, w)
