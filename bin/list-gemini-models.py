#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["google-genai", "rich"]
# ///
import os
import re
import sys
from google import genai
from rich.console import Console
from rich.table import Table

import shutil

if os.environ.get("COLUMNS") == "80":
    os.environ.pop("COLUMNS", None)
_term_width = shutil.get_terminal_size((140, 24)).columns
console = Console(width=max(_term_width, 140))

SCRIPT_PATH = "~/git/gemini-tools/bin/list-gemini-models.py"
CHANGELOG_URL = "https://ai.google.dev/gemini-api/docs/changelog"
MODELS_DOCS_URL = "https://ai.google.dev/gemini-api/docs/models"

# Official release dates from Gemini API Release Notes (ai.google.dev/gemini-api/docs/changelog)
# Necessary because generativelanguage.googleapis.com/v1beta/models only populates
# tuned_model_info.create_time for user-tuned models (leaving it None on base models).
KNOWN_RELEASE_DATES = {
    "gemini-4-argon": "2026-10-13",
    "gemini-nano-banana-2.1": "2026-10-06",
    "gemini-3.8-flash-tts": "2026-09-22",
    "gemini-3.8-flash-lite-tts": "2026-09-22",
    "antigravity-preview-09-2026": "2026-09-17",
    "gemini-3.8-live": "2026-09-15",
    "gemini-3.8-live-extended-thinking": "2026-09-15",
    "lyria-3.5": "2026-09-03",
    "gemini-3.8-flash": "2026-09-02",
    "gemini-omni-1.1-flash": "2026-08-27",
    "gemini-3.5-transcribe": "2026-08-26",
    "gemini-3.5-transcribe-live": "2026-08-26",
    "gemini-3.7-flash": "2026-08-13",
    "gemini-robotics-er-2-preview": "2026-07-30",
    "gemini-robotics-er-2-streaming-preview": "2026-07-30",
    "gemini-3.6-flash": "2026-07-21",
    "gemini-3.5-flash-lite": "2026-07-21",
    "gemini-omni-flash-preview": "2026-06-30",
    "gemini-3.1-flash-lite-image": "2026-06-30",
    "gemini-3.5-live-translate-preview": "2026-06-01",
    "gemini-3.1-flash-image": "2026-05-28",
    "gemini-3-pro-image": "2026-05-28",
    "gemini-3.5-flash": "2026-05-19",
    "antigravity-preview-05-2026": "2026-05-19",
    "gemini-3.1-flash-lite": "2026-05-07",
    "gemini-embedding-2": "2026-04-22",
    "deep-research-preview-04-2026": "2026-04-21",
    "deep-research-max-preview-04-2026": "2026-04-21",
    "gemini-3.1-flash-tts-preview": "2026-04-15",
    "gemma-4-26b-a4b-it": "2026-04-02",
    "gemma-4-31b-it": "2026-04-02",
    "veo-3.1-lite-generate-preview": "2026-03-31",
    "gemini-3.1-flash-live-preview": "2026-03-26",
    "lyria-3-clip-preview": "2026-03-25",
    "lyria-3-pro-preview": "2026-03-25",
    "gemini-embedding-2-preview": "2026-03-10",
    "gemini-3.1-flash-lite-preview": "2026-03-03",
    "gemini-3.1-flash-image-preview": "2026-02-26",
    "gemini-3.1-pro-preview": "2026-02-19",
    "gemini-3.1-pro-preview-customtools": "2026-02-19",
    "gemini-3-flash-preview": "2025-12-17",
    "gemini-2.5-flash-native-audio-preview-12-2025": "2025-12-12",
    "deep-research-pro-preview-12-2025": "2025-12-11",
    "gemini-3-pro-image-preview": "2025-11-20",
    "nano-banana-pro-preview": "2025-11-20",
    "veo-3.1-generate-preview": "2025-10-15",
    "veo-3.1-fast-generate-preview": "2025-10-15",
    "gemini-2.5-computer-use-preview-10-2025": "2025-10-01",
    "gemini-robotics-er-1.5-preview": "2025-09-25",
    "gemini-2.5-flash-native-audio-preview-09-2025": "2025-09-01",
    "gemini-2.5-flash-image": "2025-08-26",
    "imagen-4.0-generate-001": "2025-08-14",
    "imagen-4.0-ultra-generate-001": "2025-08-14",
    "imagen-4.0-fast-generate-001": "2025-08-14",
    "veo-3.0-generate-001": "2025-07-29",
    "veo-3.0-fast-generate-001": "2025-07-29",
    "gemini-2.5-flash-lite": "2025-07-22",
    "gemini-embedding-001": "2025-07-01",
    "gemini-2.5-pro": "2025-06-17",
    "gemini-2.5-flash": "2025-06-17",
    "gemma-3n-e4b-it": "2025-05-20",
    "gemma-3n-e2b-it": "2025-05-20",
    "lyria-realtime-exp": "2025-05-20",
    "gemini-2.5-flash-preview-tts": "2025-05-19",
    "gemini-2.5-pro-preview-tts": "2025-05-19",
    "veo-2.0-generate-001": "2025-04-09",
    "gemma-3-1b-it": "2025-03-12",
    "gemma-3-4b-it": "2025-03-12",
    "gemma-3-12b-it": "2025-03-12",
    "gemma-3-27b-it": "2025-03-12",
    "aqa": "2024-04-09",
}

MONTH_MAP = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}


def get_model_release_date(model) -> str:
    """Resolves model creation/release date from tuned_model_info, known release map, or version/description strings."""
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


def format_unknown_dates_todo(
    unknown_models: list[str],
    script_path: str = SCRIPT_PATH,
    as_comment: bool = False,
) -> str:
    """Formats an actionable self-healing TODO footer for AI agents when unknown model dates are detected."""
    if not unknown_models:
        return ""
    models_csv = ", ".join(unknown_models)
    lines = [
        f"(*) TODO(Gemini): Found {len(unknown_models)} model(s) with UNKNOWN release date: {models_csv}",
        f"    1. Scrape latest release notes at {CHANGELOG_URL} (or {MODELS_DOCS_URL}) to get the release date (YYYY-MM-DD).",
        f"    2. Put it back into KNOWN_RELEASE_DATES in {script_path}",
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
  [cyan]search_term[/cyan]    Optional string to filter models by name or description (e.g., 'argon', 'veo', 'lyria').

[yellow]Flags:[/yellow]
  [cyan]--full[/cyan]         Display full table including release date, supported actions, version, and description.
  [cyan]--by-date[/cyan]      Sort models by release date (newest first) instead of alphabetically.
  [cyan]-n, --max-items N[/cyan] Limit output to the first N models (e.g. `-n 10` for the 10 newest with `--by-date`).
  [cyan]--ai-help[/cyan]      Output Markdown instructions for AI agents (including self-healing release dates).
  [cyan]-h, --help[/cyan]     Show this help message.

[yellow]Examples:[/yellow]
  list-gemini-models.py                        # List all models in bash-friendly format
  list-gemini-models.py veo                    # List only Veo models
  list-gemini-models.py --full                 # Show full table of all models (with release dates)
  list-gemini-models.py --full --by-date -n 10 # Show full table of the 10 newest models
  list-gemini-models.py --ai-help              # Show AI-friendly Markdown instructions

[dim]Note: Requires GEMINI_API_KEY environment variable.[/dim]
"""


def print_help():
    console.print(get_help_text())


def get_ai_help_markdown() -> str:
    return f"""# AI Help — `list-gemini-models.py`

## 1. Uses of the CLI for AI vs Human

- **Default mode (`list-gemini-models.py [filter]`)**: Emits bash-parsable lines (`🟣 <model-id>\\t# <emoji> <Display Name> (<YYYY-MM-DD>)`) suitable for piping into `grep`, `awk`, or shell loops.
- **Full table mode (`list-gemini-models.py --full --by-date`)**: Renders a Rich table sorted from newest to oldest release date (`📅 Released`), including `Supported Actions` and `Thinking` capability.
- **When an AI agent is asked for the "latest" or "newest" Gemini model**: Run `list-gemini-models.py --full --by-date` and inspect the top rows alongside any `UNKNOWN (*)` entries at the bottom.

## 2. Added Context & Architecture

- **Canonical Script Location**: `{SCRIPT_PATH}`
- **Symlink Wrapper**: `~/git/gic/bin/gemini-list-models.py` -> `~/git/gic/bin/list-gemini-models.py` -> `{SCRIPT_PATH}`
- **Test Suite**: `~/git/gemini-tools/tests/test_eval_dataset.py` (run via `just test` in `~/git/gemini-tools`)
- **Why `KNOWN_RELEASE_DATES` Exists**: The public `generativelanguage.googleapis.com/v1beta/models` protobuf (`Model`) does not expose a `create_time` field for foundation models (`tuned_model_info.create_time` is only populated on fine-tuned models). Therefore, `get_model_release_date(model)` resolves dates via a 4-tier fallback:
  1. `model.tuned_model_info.create_time` (if present)
  2. `KNOWN_RELEASE_DATES` dictionary in `{SCRIPT_PATH}`
  3. Regex extraction from `version`, `name`, `display_name`, and `description` (ISO `YYYY-MM-DD`, `Month DD, YYYY`, `MM-YYYY`, or `Month YYYY`)
  4. Returns `UNKNOWN (*)` if no date can be inferred (except `-latest` rolling aliases, which return `rolling`).

## 3. Self-Healing Playbook for `UNKNOWN (*)` Models

Whenever a newly released model (e.g. `gemini-4.1`) appears in the API without a date in its `version`/`description`, the CLI marks its `📅 Released` column as `UNKNOWN (*)` and prints a `(*) TODO(Gemini)` footer.

**As an AI agent, follow these exact steps to self-heal the script:**
1. Fetch the official Gemini API Release Notes from `{CHANGELOG_URL}` (or `{MODELS_DOCS_URL}`; if inside Google3, check `//depot/google3/alkali/apps/makersuite/launchpad/googledevai/en/gemini-api/docs/changelog.md`).
2. Find the exact release date (`YYYY-MM-DD`) for each model listed in the `(*) TODO(Gemini)` message.
3. Add `"<model-id>": "YYYY-MM-DD"` to `KNOWN_RELEASE_DATES` in `{SCRIPT_PATH}` (ordered newest-first).
4. Bump `~/git/gemini-tools/VERSION`, document the update in `~/git/gemini-tools/CHANGELOG.md`, and run `just test` inside `~/git/gemini-tools`.
"""


def print_ai_help():
    print(get_ai_help_markdown())

def get_emojis(model):
    emojis = []
    name_lower = model.name.lower()
    display_lower = model.display_name.lower() if model.display_name else ""
    
    # Safely convert supported actions to a single lowercase string for easy matching
    actions_str = " ".join(model.supported_actions).lower() if model.supported_actions else ""

    # Audio / Bidi / Lyria checks
    if 'bidigeneratecontent' in actions_str:
        emojis.append("🎙️") # Live/Audio
    elif 'audio' in name_lower or 'audio' in display_lower or 'lyria' in name_lower:
        emojis.append("🎵") # Music/Audio
        
    # Image / Vision / Nano Banana checks
    if 'image' in name_lower or 'image' in display_lower or 'banana' in name_lower or 'banana' in display_lower or 'vision' in name_lower or 'predict' in actions_str:
        emojis.append("🖼️")
        
    # Video checks (Veo / Omni)
    if 'video' in name_lower or 'video' in display_lower or 'veo' in name_lower or 'omni' in name_lower:
        emojis.append("🎥")
        
    # Embedding checks
    if 'embed' in name_lower or 'embed' in display_lower:
        emojis.append("🔢")
        
    # Thinking check
    if hasattr(model, 'thinking') and model.thinking:
        emojis.append("🧠")

    # Default for text/chat if no special features detected
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
            # Filter by search term if provided
            if search_term:
                name_lower = model.name.lower()
                display_lower = model.display_name.lower() if model.display_name else ""
                description_lower = model.description.lower() if model.description else ""
                if search_term not in name_lower and search_term not in display_lower and search_term not in description_lower:
                    continue # Skip this model if it doesn't match
                    
            models.append(model)
                
        if not models:
            console.print(f"[yellow]No models found matching '{search_term}'[/yellow]")
            return

        if sort_by_date:
            models.sort(key=_date_sort_key, reverse=True)
        else:
            # Sort models alphabetically by their clean name
            models.sort(key=lambda m: m.name.replace("models/", ""))

        if max_items is not None:
            models = models[:max_items]

        unknown_models: list[str] = []

        if show_full:
            # Table view for --full
            table = Table(title=f"Available GenAI Models" + (f" (matching '{search_term}')" if search_term else ""))
            table.add_column("Model Name", style="magenta", no_wrap=True)
            table.add_column("Display Name", style="cyan")
            table.add_column("📅 Released", style="bright_blue", justify="center", no_wrap=True)
            table.add_column("Ver.", style="yellow")
            table.add_column("🧠", justify="center")
            table.add_column("Supported Actions", style="green")
            table.add_column("Description", style="white")
            
            for model in models:
                emojis = get_emojis(model)
                display_name = f"{emojis} {model.display_name}" if model.display_name else f"{emojis} {model.name}"
                clean_name = model.name.replace("models/", "", 1)
                release_date = get_model_release_date(model)
                if release_date == "UNKNOWN (*)":
                    unknown_models.append(clean_name)
                    release_display = "[bold yellow]UNKNOWN (*)[/bold yellow]"
                else:
                    release_display = release_date
                actions_display = ", ".join(model.supported_actions) if model.supported_actions else "None"
                version = model.version if hasattr(model, 'version') else "-"
                thinking = "✅" if hasattr(model, 'thinking') and model.thinking else "❌"
                description = model.description if model.description else "-"
                
                table.add_row(clean_name, display_name, release_display, version, thinking, actions_display, description)
            
            console.print(table)
            if unknown_models:
                console.print(f"\n[bold yellow]{format_unknown_dates_todo(unknown_models)}[/bold yellow]")
        else:
            # Bash-parsable view
            for model in models:
                emojis = get_emojis(model)
                display_name = f"{emojis} {model.display_name}" if model.display_name else f"{emojis} {model.name}"
                clean_name = model.name.replace("models/", "", 1)
                release_date = get_model_release_date(model)
                if release_date == "UNKNOWN (*)":
                    unknown_models.append(clean_name)
                date_suffix = f" ({release_date})" if release_date != "-" else ""
                
                # Output format: 🟣 model-name \t # ✨ Emojiful Description (YYYY-MM-DD)
                # Use rich to print the comment part in dim (gray) color
                console.print(f"🟣 {clean_name}\t[dim]# {display_name}{date_suffix}[/dim]")
                
            console.print("\n[dim]# 💡 Invoke with --full (and optionally --by-date) to see release dates, supported actions, and more info as a table.[/dim]")
            if unknown_models:
                console.print(f"[yellow]{format_unknown_dates_todo(unknown_models, as_comment=True)}[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error listing models: {e}[/red]")

if __name__ == "__main__":
    main()
