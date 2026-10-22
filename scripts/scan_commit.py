"""G5 scanner: block secrets, real names, personal paths, e-mail addresses and local data before a commit.

Scans every file git would include (tracked plus untracked, not ignored). Real colleague names
come from a denylist kept outside the repository (.Codex/kontext/scan-denylist.txt, ignored),
so the names themselves never enter git. Findings print path, line and rule, never the value.
Exit 1 on findings, 0 otherwise.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DENYLIST = ROOT / ".Codex" / "kontext" / "scan-denylist.txt"

_FORBIDDEN_PREFIXES = ("data/", ".harness/", "test-results/", ".Codex/kontext/", ".claude/kontext/")
_FORBIDDEN_SUFFIX = re.compile(r"\.(db|sqlite3?)(-\w+)?$", re.IGNORECASE)
_SECRETS = tuple(re.compile(pattern) for pattern in (
    r"\bgh[pousr]_[A-Za-z0-9]{36,}",
    r"\bgithub_pat_[A-Za-z0-9_]{22,}",
    r"\bAKIA[0-9A-Z]{16}\b",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bsk-[A-Za-z0-9_-]{20,}",
    r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    r"\bKUMI_SECRET_KEY\s*=\s*\S{8,}",
    r"(?i)\b(password|passwort|secret|api_key)\s*[:=]\s*[\"'][^\"'\s]{6,}[\"']",
))
_PERSONAL_PATH = re.compile(r"(?i)\b[a-z]:(?:\\+|/)users(?:\\+|/)[^\\/\s\"']+|/(?:home|Users)/[a-z][\w.-]*/")
_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
_ALLOWED_EMAIL_DOMAINS = ("anthropic.com", "example.com", "example.org", "example.net")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    detail: str


def _forbidden(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return True
    if name == "settings.local.json":
        return True
    return path.startswith(_FORBIDDEN_PREFIXES) or bool(_FORBIDDEN_SUFFIX.search(name))


def _email_allowed(domain: str) -> bool:
    domain = domain.lower()
    return domain.endswith(".invalid") or domain.endswith(".test") or any(
        domain == allowed or domain.endswith("." + allowed) for allowed in _ALLOWED_EMAIL_DOMAINS)


def scan(root: Path, paths: list[str], denylist: list[str]) -> list[Finding]:
    """Return findings for the given repository-relative paths."""
    names = [(name, re.compile(r"(?<!\w)" + re.escape(name) + r"(?!\w)", re.IGNORECASE)) for name in denylist]
    findings: list[Finding] = []
    for path in sorted(paths):
        posix = path.replace("\\", "/")
        if _forbidden(posix):
            findings.append(Finding(posix, 0, "forbidden-file", "lokale Daten/Kontext gehören nicht ins Repository"))
            continue
        try:
            raw = (Path(root) / path).read_bytes()
        except OSError:
            continue
        if b"\x00" in raw:
            continue  # Binary file.
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in _SECRETS):
                findings.append(Finding(posix, number, "secret", "Zugangsdaten-/Schlüsselmuster"))
            if _PERSONAL_PATH.search(line):
                findings.append(Finding(posix, number, "personal-path", "persönlicher Benutzerpfad"))
            if any(not _email_allowed(match.group(1)) for match in _EMAIL.finditer(line)):
                findings.append(Finding(posix, number, "email", "E-Mail-Adresse außerhalb erlaubter Beispiel-Domains"))
            for name, pattern in names:
                if pattern.search(line):
                    findings.append(Finding(posix, number, "real-name", "Name aus der Sperrliste"))
                    break
    return findings


def load_denylist(path: Path) -> tuple[list[str], str | None]:
    """Read real names (one per line, # comments) from a file outside the repository."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return [], (f"Hinweis: keine Sperrliste echter Namen gefunden ({path}). "
                    "Namensprüfung übersprungen; Datei anlegen, um sie zu aktivieren.")
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")], None


def repository_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=root,
                            capture_output=True, text=True, encoding="utf-8", check=True)
    return [line for line in result.stdout.splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--denylist", type=Path, default=DEFAULT_DENYLIST)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    names, warning = load_denylist(args.denylist)
    if warning:
        print(warning)
    files = repository_files(args.root)
    findings = scan(args.root, files, names)
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.rule} ({finding.detail})")
    print(f"G5-Scan: {len(files)} Dateien, {len(findings)} Funde.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
