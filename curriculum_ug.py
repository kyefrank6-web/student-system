"""
Uganda National Curriculum structure for learner placement.
Primary: P1–P7. Secondary: S1–S6 (O-level S1–S4, A-level S5–S6).
"""

# (code, label) — codes are stored on Student.class_level
UG_CLASS_LEVELS = [
    ("P1", "Primary 1 (P1)"),
    ("P2", "Primary 2 (P2)"),
    ("P3", "Primary 3 (P3)"),
    ("P4", "Primary 4 (P4)"),
    ("P5", "Primary 5 (P5)"),
    ("P6", "Primary 6 (P6)"),
    ("P7", "Primary 7 (P7)"),
    ("S1", "Secondary 1 — O-level (S1)"),
    ("S2", "Secondary 2 — O-level (S2)"),
    ("S3", "Secondary 3 — O-level (S3)"),
    ("S4", "Secondary 4 — O-level (S4)"),
    ("S5", "Secondary 5 — A-level (S5)"),
    ("S6", "Secondary 6 — A-level (S6)"),
]

UG_CLASS_CODES = frozenset(code for code, _ in UG_CLASS_LEVELS)

UG_PRIMARY_CODES = frozenset(f"P{i}" for i in range(1, 8))
UG_SECONDARY_CODES = frozenset(f"S{i}" for i in range(1, 7))

UG_PRIMARY_LEVELS = [(c, lbl) for c, lbl in UG_CLASS_LEVELS if c.startswith("P")]
UG_SECONDARY_LEVELS = [(c, lbl) for c, lbl in UG_CLASS_LEVELS if c.startswith("S")]


def label_for_code(code: str) -> str:
    for c, lbl in UG_CLASS_LEVELS:
        if c == code:
            return lbl
    return code or "—"
