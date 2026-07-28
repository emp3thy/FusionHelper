import adsk.core


def run(_context: str):
    v = adsk.core.ValueInput.createByString("60 mm")
    print(v)
