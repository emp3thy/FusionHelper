from dataclasses import dataclass


@dataclass(frozen=True)
class RuleInfo:
    rule_id: str
    number: str
    restatement: str
    checked: bool  # False for R3/R9 — runtime/convention; named in the coverage line


@dataclass(frozen=True)
class Finding:
    rule_id: str
    rule_number: str
    line: int
    col: int
    severity: str  # "error" | "warn"
    message: str
    fix: str | None = None


RULES: dict[str, RuleInfo] = {
    "R1": RuleInfo("no-create-by-real", "R1",
                   "Never ValueInput.createByReal — use createByString, always", True),
    "R2": RuleInfo("dimension-must-bind", "R2",
                   "Every sketchDimensions.add* must have .parameter.expression assigned", True),
    "R3": RuleInfo("constrain-then-dimension", "R3",
                   "Constrain, check isFullyConstrained, dimension the residual (runtime)", False),
    "R4": RuleInfo("no-index-topology", "R4",
                   "Never select topology by index — geometric predicate or entityToken", True),
    "R5": RuleInfo("no-stale-brep", "R5",
                   "Never use a BRep reference across a parameter change", True),
    "R6": RuleInfo("no-hardcoded-axis", "R6",
                   "Derive axis mapping from sketchToModelSpace() at runtime", True),
    "R7": RuleInfo("param-name-safe", "R7",
                   "Parameter names are multi-character snake_case", True),
    "R8": RuleInfo("verify-stub-intact", "R8",
                   "The file ends with the verification stub, unmodified", True),
    "R9": RuleInfo("no-catch", "R9",
                   "Never catch exceptions in generated scripts (convention)", False),
    "R10": RuleInfo("no-save", "R10",
                    "Never save the document — checkpoint saves need a waiver "
                    "naming user consent", True),
    "R11": RuleInfo("loops-must-breathe", "R11",
                    "Loops that mutate the document call adsk.doEvents() "
                    "per iteration", True),
}
BY_ID = {info.rule_id: info for info in RULES.values()}
