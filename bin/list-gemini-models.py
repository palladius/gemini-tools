#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["google-genai", "rich"]
# ///
import os
import re
import shutil
import sys
from pathlib import Path
from google import genai
from rich.console import Console
from rich.table import Table

if os.environ.get("COLUMNS") == "80":
    os.environ.pop("COLUMNS", None)
_term_width = shutil.get_terminal_size((140, 24)).columns
console = Console(width=max(_term_width, 140))

SCRIPT_PATH = "~/git/gemini-tools/bin/list-gemini-models.py"
YAML_REL_PATH = "etc/gemini_models.yaml"
YAML_DISPLAY_PATH = "~/git/gemini-tools/etc/gemini_models.yaml"
CHANGELOG_URL = "https://ai.google.dev/gemini-api/docs/changelog"
MODELS_DOCS_URL = "https://ai.google.dev/gemini-api/docs/models"

MONTH_MAP = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05", "june": "06", "jun": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}


def _parse_simple_models_yaml(text: str) -> dict[str, dict[str, str]]:
    """Zero-dependency parser for etc/gemini_models.yaml so PEP-723 script & stdlib tests need no PyYAML."""
    catalog: dict[str, dict[str, str]] = {}
    current_model: str | None = None
    in_models = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "models:":
            in_models = True
            continue
        if not in_models:
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 2 and stripped.endswith(":"):
            current_model = stripped[:-1].strip()
            catalog[current_model] = {}
        elif indent >= 4 and current_model and ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            catalog[current_model][k] = v
    return catalog


def load_models_catalog(yaml_path: Path | None = None) -> dict[str, dict[str, str]]:
    """Loads the curated model catalog (release_date, category, twitter_description) from etc/gemini_models.yaml."""
    if yaml_path is None:
        yaml_path = Path(__file__).resolve().parent.parent / "etc" / "gemini_models.yaml"
    if not yaml_path.exists():
        return {}
    return _parse_simple_models_yaml(yaml_path.read_text(encoding="utf-8"))


MODELS_CATALOG = load_models_catalog()
KNOWN_RELEASE_DATES = {k: v.get("release_date", "UNKNOWN (*)") for k, v in MODELS_CATALOG.items() if "release_date" in v}


def get_model_release_date(model) -> str:
    """Resolves model creation/release date from tuned_model_info, etc/gemini_models.yaml, or version/description strings."""
    t_info = getattr(model, "tuned_model_info", None)
    create_time = getattr(t_info, "create_time", None) if t_info else None
    if create_time:
        return create_time.strftime("%Y-%m-%d") if hasattr(create_time, "strftime") else str(create_time)[:10]

    clean_name = (getattr(model, "name", "") or "").replace("models/", "", 1)
    if clean_name in KNOWN_RELEASE_DATES:
        return KNOWN_RELEASE_DATES[clean_name]

    if clean_name.endswith("-latest"):
        return "rolling"

    blob = " | ".join(
        str(getattr(model, attr, "") or "")
        for attr in ("version", "name", "display_name", "description")
    )

    # 1. Explicit ISO date YYYY-MM-DD (e.g. 2025-05-19)
    m_iso = re.search(r"\b(20\d{2})-(0[1-9]|1[0-2])-([0-2]\d|3[01])\b", blob)
    if m_iso:
        return f"{m_iso.group(1)}-{m_iso.group(2)}-{m_iso.group(3)}"

    # 2. Month-Day-Year in display_name/description (e.g. Apr-21-2026 or April 21st, 2026)
    m_mdy = re.search(
        r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[-\s]+(\d{1,2})(?:st|nd|rd|th)?,?[-\s]+(20\d{2})\b",
        blob,
        re.IGNORECASE,
    )
    if m_mdy:
        month = MONTH_MAP[m_mdy.group(1).lower()[:3]]
        day = int(m_mdy.group(2))
        return f"{m_mdy.group(3)}-{month}-{day:02d}"

    # 3. MM-YYYY in version or model name (e.g. 08-2026, 12-2025)
    m_my = re.search(r"(?:^|[-_(\s])(0[1-9]|1[0-2])-(20\d{2})(?:\b|[)_])", blob)
    if m_my:
        return f"{m_my.group(2)}-{m_my.group(1)}"

    # 4. Prose "released in July of 2025"
    m_prose = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:of\s+)?(20\d{2})\b",
        blob,
        re.IGNORECASE,
    )
    if m_prose:
        month = MONTH_MAP[m_prose.group(1).lower()[:3]]
        return f"{m_prose.group(2)}-{month}"

    return "UNKNOWN (*)"


def get_model_twitter_description(model) -> str:
    """Returns the punchy (<280B) twitter_description from etc/gemini_models.yaml, or 'UNKNOWN (*)' if unmapped."""
    clean_name = (getattr(model, "name", "") or "").replace("models/", "", 1)
    entry = MODELS_CATALOG.get(clean_name, {})
    desc = entry.get("twitter_description", "").strip()
    if desc:
        return desc
    return "UNKNOWN (*)"


def format_unknown_dates_todo(
    unknown_models: list[str],
    yaml_path: str = YAML_DISPLAY_PATH,
    as_comment: bool = False,
) -> str:
    """Formats an actionable self-healing TODO footer for AI agents when unknown model dates or twitter_descriptions are detected."""
    if not unknown_models:
        return ""
    models_csv = ", ".join(unknown_models)
    lines = [
        f"(*) TODO(Gemini): Found {len(unknown_models)} model(s) missing release_date or twitter_description: {models_csv}",
        f"    1. Scrape latest release notes & capabilities at {CHANGELOG_URL} (or {MODELS_DOCS_URL}).",
        f"    2. Add 'release_date' (YYYY-MM-DD) and a punchy 'twitter_description' (<=280B) to {yaml_path} ({YAML_REL_PATH}).",
        f"    3. Run `list-gemini-models.py --ai-help` for the step-by-step AI self-healing instructions.",
    ]
    if as_comment:
        return "\n".join(f"# {line}" for line in lines)
    return "\n".join(lines)


def get_help_text() -> str:
    return """
[bold]Google GenAI Model Lister[/bold]

[yellow]Usage:[/yellow]
  list-gemini-models.py [search_term] [flags]

[yellow]Arguments:[/yellow]
  [cyan]search_term[/cyan]    Optional string to filter models by name, description, or twitter_description (e.g., 'argon', 'omni', 'lyria').

[yellow]Flags:[/yellow]
  [cyan]--full[/cyan]             Display full table including release date, supported actions, version, and Twitter description.
  [cyan]--by-date[/cyan]          Sort models by release date (newest first) instead of alphabetically.
  [cyan]-n, --max-items N[/cyan]  Limit output to the first N models (e.g. `-n 10` for the 10 newest with `--by-date`).
  [cyan]--ai-help[/cyan]          Output Markdown instructions for AI agents (including self-healing YAML catalog).
  [cyan]-h, --help[/cyan]         Show this help message.

[yellow]Examples:[/yellow]
  list-gemini-models.py                        # List all models in bash-friendly format
  list-gemini-models.py veo                    # List only Veo models
  list-gemini-models.py --full                 # Show full table of all models (with release dates & Twitter descriptions)
  list-gemini-models.py --full --by-date -n 10 # Show full table of the 10 newest models
  list-gemini-models.py --ai-help              # Show AI-friendly Markdown instructions

[dim]Note: Requires GEMINI_API_KEY environment variable.[/dim]
"""


def print_help():
    console.print(get_help_text())


def get_ai_help_markdown() -> str:
    return f"""# AI Help — `list-gemini-models.py`

## 1. Uses of the CLI for AI vs Human

- **Default mode (`list-gemini-models.py [filter]`)**: Emits bash-parsable lines (`🟣 <model-id>\\t# <emoji> <Display Name> (<YYYY-MM-DD>) — <twitter_description>`) suitable for piping into `grep`, `awk`, or shell loops.
- **Full table mode (`list-gemini-models.py --full --by-date -n 10`)**: Renders a Rich table sorted from newest to oldest release date (`📅 Released`), including `Supported Actions`, `Thinking`, and a curated `<280B` `🐦 What It Does (Twitter Desc)` column.
- **When an AI agent is asked for the "latest" or "newest" Gemini model**: Run `list-gemini-models.py --full --by-date -n 10` and inspect the top rows alongside any `UNKNOWN (*)` entries.

## 2. Added Context & Architecture

- **Canonical Script Location**: `{SCRIPT_PATH}`
- **Curated YAML Catalog**: `{YAML_DISPLAY_PATH}` (`{YAML_REL_PATH}`)
- **Symlink Wrapper**: `~/git/gic/bin/gemini-list-models.py` -> `~/git/gic/bin/list-gemini-models.py` -> `{SCRIPT_PATH}`
- **Test Suite**: `~/git/gemini-tools/tests/test_eval_dataset.py` (run via `just test` in `~/git/gemini-tools`)
- **Why `{YAML_REL_PATH}` Exists**:
  1. The public `generativelanguage.googleapis.com/v1beta/models` protobuf (`Model`) does not expose a `create_time` field for foundation models (`tuned_model_info.create_time` is only populated on fine-tuned models).
  2. The API `description` field on newer models merely repeats the display name (e.g. `"Gemini 4 Argon"` or `"Gemini Omni 1.1 Flash"`) without explaining what the model actually does or which SDK endpoint it requires (`client.interactions` vs `generateContent`).
  3. Therefore, `{YAML_DISPLAY_PATH}` is the single source of truth for each model's `release_date`, `category`, and punchy (`<=280` bytes) `twitter_description`.

## 3. Self-Healing Playbook for `UNKNOWN (*)` Models

Whenever a newly released model (e.g. `gemini-4.1`) appears in the API without a `release_date` or `twitter_description` in `{YAML_DISPLAY_PATH}`, the CLI marks the missing field as `UNKNOWN (*)` and prints a `(*) TODO(Gemini)` footer.

**As an AI agent, follow these exact steps to self-heal the catalog:**
1. Fetch the official Gemini API Release Notes from `{CHANGELOG_URL}` and `{MODELS_DOCS_URL}` (if inside Google3, check `//depot/google3/alkali/apps/makersuite/launchpad/googledevai/en/gemini-api/docs/changelog.md`).
2. For each model listed in the `(*) TODO(Gemini)` message, add an entry under `models:` in `{YAML_DISPLAY_PATH}` with:
   - `release_date: "YYYY-MM-DD"` (or `"rolling"` for `-latest` aliases)
   - `category: "<category>"`
   - `twitter_description: "<punchy <=280 byte summary of what it does, limits, and API endpoint>"`
3. Bump `~/git/gemini-tools/VERSION`, document the update in `~/git/gemini-tools/CHANGELOG.md`, and run `just test` inside `~/git/gemini-tools`.
"""


def print_ai_help():
    print(get_ai_help_markdown())


def get_emojis(model):
    emojis = []
    name_lower = model.name.lower()
    display_lower = model.display_name.lower() if model.display_name else ""
    actions_str = " ".join(model.supported_actions).lower() if model.supported_actions else ""

    if "bidigeneratecontent" in actions_str:
        emojis.append("🎙️")
    elif "audio" in name_lower or "audio" in display_lower or "lyria" in name_lower:
        emojis.append("🎵")

    if (
        "image" in name_lower
        or "image" in display_lower
        or "banana" in name_lower
        or "banana" in display_lower
        or "vision" in name_lower
        or "predict" in actions_str
    ):
        emojis.append("🖼️")

    if "video" in name_lower or "video" in display_lower or "veo" in name_lower or "omni" in name_lower:
        emojis.append("🎥")

    if "embed" in name_lower or "embed" in display_lower:
        emojis.append("🔢")

    if hasattr(model, "thinking") and model.thinking:
        emojis.append("🧠")

    if not emojis:
        emojis.append("✨")

    return "".join(emojis)


def _date_sort_key(model) -> tuple[str, str]:
    rel = get_model_release_date(model)
    clean_name = model.name.replace("models/", "", 1)
    if rel == "UNKNOWN (*)":
        return ("9999-99-99", clean_name)
    if rel in ("-", "rolling"):
        return ("0000-00-00", clean_name)
    return (rel, clean_name)


def _resolve_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    for candidate in (
        os.path.expanduser("~/git/gemini-tools/.env"),
        os.path.expanduser("~/git/gic/.bashrc"),
    ):
        if os.path.exists(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    content = f.read()
                m = re.search(r'^\s*(?:export\s+)?GEMINI_API_KEY=["\']?([^"\'\s#]+)["\']?', content, re.MULTILINE)
                if m:
                    return m.group(1)
            except OSError:
                pass
    return None


def main():
    if "--ai-help" in sys.argv:
        print_ai_help()
        sys.exit(0)

    if "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    api_key = _resolve_api_key()
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable not set.[/red]")
        sys.exit(1)

    show_full = "--full" in sys.argv
    sort_by_date = "--by-date" in sys.argv
    max_items = None
    skip_next = False
    search_term = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if arg in ("-n", "--max-items", "--limit") and i + 1 < len(args):
            try:
                max_items = int(args[i + 1])
            except ValueError:
                pass
            skip_next = True
        elif arg.startswith("--max-items=") or arg.startswith("--limit="):
            try:
                max_items = int(arg.split("=", 1)[1])
            except ValueError:
                pass
        elif not arg.startswith("-") and search_term is None:
            search_term = arg.lower()

    client = genai.Client(api_key=api_key)

    try:
        models = []
        for model in client.models.list():
            if search_term:
                name_lower = model.name.lower()
                display_lower = model.display_name.lower() if model.display_name else ""
                description_lower = model.description.lower() if model.description else ""
                tw_lower = get_model_twitter_description(model).lower()
                if (
                    search_term not in name_lower
                    and search_term not in display_lower
                    and search_term not in description_lower
                    and search_term not in tw_lower
                ):
                    continue

            models.append(model)

        if not models:
            console.print(f"[yellow]No models found matching '{search_term}'[/yellow]")
            return

        if sort_by_date:
            models.sort(key=_date_sort_key, reverse=True)
        else:
            models.sort(key=lambda m: m.name.replace("models/", ""))

        if max_items is not None:
            models = models[:max_items]

        unknown_models: list[str] = []

        if show_full:
            table = Table(title="Available GenAI Models" + (f" (matching '{search_term}')" if search_term else ""))
            table.add_column("Model Name", style="magenta", no_wrap=True)
            table.add_column("Display Name", style="cyan")
            table.add_column("📅 Released", style="bright_blue", justify="center", no_wrap=True)
            table.add_column("Ver.", style="yellow")
            table.add_column("🧠", justify="center")
            table.add_column("Supported Actions", style="green")
            table.add_column("🐦 What It Does (Twitter Desc)", style="white")

            for model in models:
                emojis = get_emojis(model)
                display_name = f"{emojis} {model.display_name}" if model.display_name else f"{emojis} {model.name}"
                clean_name = model.name.replace("models/", "", 1)
                release_date = get_model_release_date(model)
                twitter_desc = get_model_twitter_description(model)

                if release_date == "UNKNOWN (*)" or twitter_desc == "UNKNOWN (*)":
                    unknown_models.append(clean_name)

                release_display = "[bold yellow]UNKNOWN (*)[/bold yellow]" if release_date == "UNKNOWN (*)" else release_date
                desc_display = "[bold yellow]UNKNOWN (*)[/bold yellow]" if twitter_desc == "UNKNOWN (*)" else twitter_desc
                actions_display = ", ".join(model.supported_actions) if model.supported_actions else "None"
                version = model.version if hasattr(model, "version") else "-"
                thinking = "✅" if hasattr(model, "thinking") and model.thinking else "❌"

                table.add_row(clean_name, display_name, release_display, version, thinking, actions_display, desc_display)

            console.print(table)
            if unknown_models:
                console.print(f"\n[bold yellow]{format_unknown_dates_todo(unknown_models)}[/bold yellow]")
        else:
            for model in models:
                emojis = get_emojis(model)
                display_name = f"{emojis} {model.display_name}" if model.display_name else f"{emojis} {model.name}"
                clean_name = model.name.replace("models/", "", 1)
                release_date = get_model_release_date(model)
                twitter_desc = get_model_twitter_description(model)
                if release_date == "UNKNOWN (*)" or twitter_desc == "UNKNOWN (*)":
                    unknown_models.append(clean_name)
                date_suffix = f" ({release_date})" if release_date != "-" else ""

                console.print(f"🟣 {clean_name}\t[dim]# {display_name}{date_suffix} — {twitter_desc}[/dim]")

            console.print("\n[dim]# 💡 Invoke with --full (and optionally --by-date -n 10) to see release dates, supported actions, and Twitter descriptions as a table.[/dim]")
            if unknown_models:
                console.print(f"[yellow]{format_unknown_dates_todo(unknown_models, as_comment=True)}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error listing models: {e}[/red]")


if __name__ == "__main__":
    main()
