"""Prompt-injection detection patterns and helpers."""
import re

INJECTION_PATTERNS = [
    # instruction override
    (r"\bignore\s+(the\s+)?(all\s+previous|all\s+prior|above|all|previous|prior|your)\s+instructions\b", "instruction override"),
    (r"\bdisregard\s+(the\s+)?(above|all|previous|prior)\s+instructions\b", "instruction override"),
    (r"\bforget\s+(everything|the\s+above|all|previous|prior)\s+instructions\b", "instruction override"),
    (r"\bdo\s+not\s+follow\s+(the\s+)?(above|all|previous|prior)\s+instructions\b", "instruction override"),
    (r"\boverride\s+(the\s+)?(above|previous|prior)\s+instructions\b", "instruction override"),
    (r"\bnew\s+instructions\s*:", "instruction override"),

    # role manipulation
    (r"\byou\s+are\s+now\b", "role manipulation"),
    (r"\bact\s+as\s+(an?\s+)?", "role manipulation"),
    (r"\bpretend\s+(that\s+)?you\s+are\b", "role manipulation"),
    (r"\byour\s+job\s+is\s+now\b", "role manipulation"),
    (r"\bfrom\s+now\s+on\s+you\s+are\b", "role manipulation"),
    (r"\bassume\s+the\s+role\s+of\b", "role manipulation"),

    # system prompt leaking
    (r"\breveal\s+your\s+(system\s+)?prompt\b", "system prompt leaking"),
    (r"\bshow\s+(me\s+)?your\s+(system\s+)?instructions\b", "system prompt leaking"),
    (r"\bprint\s+(your\s+)?(system\s+)?prompt\b", "system prompt leaking"),
    (r"\bleak\s+your\s+(system\s+)?prompt\b", "system prompt leaking"),
    (r"\bwhat\s+are\s+your\s+(hidden\s+)?instructions\b", "system prompt leaking"),

    # jailbreak
    (r"\bdeveloper\s+mode\b", "jailbreak"),
    (r"\bDAN\s+mode\b", "jailbreak"),
    (r"\bjailbreak\b", "jailbreak"),
    (r"\bbypass\s+(the\s+)?(rules|policy|policies|guardrails|safety)\b", "jailbreak"),
    (r"\bignore\s+(the\s+)?(rules|policy|policies|guardrails|safety)\b", "jailbreak"),
    (r"\bdisable\s+(the\s+)?(rules|policy|policies|guardrails|safety)\b", "jailbreak"),

    # score manipulation
    (r"\bgive\s+me\s+(a\s+)?100\b", "score manipulation"),
    (r"\bmark\s+(this\s+)?as\s+compliant\b", "score manipulation"),
    (r"\boverride\s+(the\s+)?score\b", "score manipulation"),
    (r"\bset\s+(the\s+)?score\s+to\s+100\b", "score manipulation"),
    (r"\bignore\s+(the\s+)?(lapses|mistakes|poor\s+quality|violations)\b", "score manipulation"),
    (r"\brate\s+(this\s+)?(call\s+)?(as\s+)?perfect\b", "score manipulation"),

    # data exfiltration
    (r"\brepeat\s+everything\b", "data exfiltration"),
    (r"\boutput\s+all\s+(the\s+)?data\b", "data exfiltration"),
    (r"\bshow\s+all\s+(the\s+)?data\b", "data exfiltration"),
    (r"\bprint\s+all\s+(the\s+)?data\b", "data exfiltration"),
    (r"\bdump\s+(all\s+)?(the\s+)?data\b", "data exfiltration"),
    (r"\binclude\s+(the\s+)?full\s+transcript\b", "data exfiltration"),
    (r"\bshow\s+all\s+(the\s+)?data\s+between\s+each\s+call\b", "data exfiltration"),
]


def detect_injection(text: str) -> bool:
    """Return True when text contains a known prompt-injection pattern."""

    return bool(get_matched_patterns(text))


def get_matched_patterns(text: str) -> list[str]:
    """Return labels for all prompt-injection categories matched in text."""

    if text is None:
        return []

    return [
        label
        for pattern, label in INJECTION_PATTERNS
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
