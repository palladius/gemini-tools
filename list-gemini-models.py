#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["google-genai", "rich"]
# ///
import os
import sys
from google import genai
from rich.console import Console
from rich.table import Table

console = Console()

def print_help():
    help_text = """
[bold]Google GenAI Model Lister[/bold]

[yellow]Usage:[/yellow]
  list-gemini-models.py [search_term] [flags]

[yellow]Arguments:[/yellow]
  [cyan]search_term[/cyan]    Optional string to filter models by name or description (e.g., '2.5', 'veo', 'lyria').

[yellow]Flags:[/yellow]
  [cyan]--full[/cyan]         Display full table including supported actions, version, and description.
  [cyan]-h, --help[/cyan]     Show this help message.

[yellow]Examples:[/yellow]
  list-gemini-models.py           # List all models in bash-friendly format
  list-gemini-models.py veo       # List only Veo models
  list-gemini-models.py --full    # Show full table of all models

[dim]Note: Requires GEMINI_API_KEY environment variable.[/dim]
"""
    console.print(help_text)

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
        
    # Image / Vision checks
    if 'image' in name_lower or 'image' in display_lower or 'vision' in name_lower or 'predict' in actions_str:
        emojis.append("🖼️")
        
    # Video checks (Veo)
    if 'video' in name_lower or 'video' in display_lower or 'veo' in name_lower:
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

def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable not set.[/red]")
        sys.exit(1)

    show_full = "--full" in sys.argv
    
    # Extract the first non-flag argument to use as a search term
    search_term = next((arg.lower() for arg in sys.argv[1:] if not arg.startswith('--') and arg != '-h'), None)

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

        # Sort models alphabetically by their clean name
        models.sort(key=lambda m: m.name.replace("models/", ""))
                
        if show_full:
            # Table view for --full
            table = Table(title=f"Available GenAI Models" + (f" (matching '{search_term}')" if search_term else ""))
            table.add_column("Model Name", style="magenta")
            table.add_column("Display Name", style="cyan")
            table.add_column("Ver.", style="yellow")
            table.add_column("🧠", justify="center")
            table.add_column("Supported Actions", style="green")
            table.add_column("Description", style="white")
            
            for model in models:
                emojis = get_emojis(model)
                display_name = f"{emojis} {model.display_name}" if model.display_name else f"{emojis} {model.name}"
                clean_name = model.name.replace("models/", "", 1)
                actions_display = ", ".join(model.supported_actions) if model.supported_actions else "None"
                version = model.version if hasattr(model, 'version') else "-"
                thinking = "✅" if hasattr(model, 'thinking') and model.thinking else "❌"
                description = model.description if model.description else "-"
                
                table.add_row(clean_name, display_name, version, thinking, actions_display, description)
            
            console.print(table)
        else:
            # Bash-parsable view
            for model in models:
                emojis = get_emojis(model)
                display_name = f"{emojis} {model.display_name}" if model.display_name else f"{emojis} {model.name}"
                clean_name = model.name.replace("models/", "", 1)
                
                # Output format: 🟣 model-name \t # ✨ Emojiful Description
                # Use rich to print the comment part in dim (gray) color
                console.print(f"🟣 {clean_name}\t[dim]# {display_name}[/dim]")
                
            console.print("\n[dim]# 💡 Invoke with --full to see supported actions and more info as a table.[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error listing models: {e}[/red]")

if __name__ == "__main__":
    main()
