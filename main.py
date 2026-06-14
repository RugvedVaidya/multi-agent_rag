"""
main.py  —  CLI interface for the Multi-Agent RAG system

Usage:
  python main.py                  # start interactive chat
  python main.py --verbose        # show agent pipeline trace
  python main.py --ingest <path>  # ingest a file or folder, then chat
"""

import sys
import argparse
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

import config

# Basic validation before anything else
if not config.GROQ_API_KEY:
    print("ERROR: GROQ_API_KEY not set. Add it to a .env file or environment.")
    sys.exit(1)

import orchestrator
from ingest import ingest_path
import chromadb

console = Console()


def db_stats() -> str:
    """Return a quick summary of what's in the vector DB."""
    try:
        db = chromadb.PersistentClient(path=config.CHROMA_DIR)
        col = db.get_or_create_collection(config.COLLECTION_NAME)
        count = col.count()
        return f"{count} chunks indexed"
    except Exception:
        return "DB not initialized"


def print_welcome():
    stats = db_stats()
    console.print(Panel(
        f"[bold cyan]Multi-Agent RAG Assistant[/bold cyan]\n"
        f"[dim]Knowledge base: {stats}[/dim]\n\n"
        f"Commands:\n"
        f"  [yellow]/ingest <path>[/yellow]  — add a file or folder to the knowledge base\n"
        f"  [yellow]/stats[/yellow]          — show DB statistics\n"
        f"  [yellow]/verbose[/yellow]        — toggle pipeline trace on/off\n"
        f"  [yellow]/clear[/yellow]          — clear conversation history\n"
        f"  [yellow]/quit[/yellow]           — exit",
        title="Welcome",
        border_style="cyan",
    ))


def chat_loop(verbose: bool = False):
    history  = []
    _verbose = verbose

    print_welcome()
    console.print()

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        # ── Commands ──────────────────────────────────────────
        if user_input.startswith("/ingest "):
            path = user_input[8:].strip()
            ingest_path(path)
            console.print(f"[dim]DB now has: {db_stats()}[/dim]\n")
            continue

        if user_input == "/stats":
            console.print(f"[dim]{db_stats()}[/dim]\n")
            continue

        if user_input == "/verbose":
            _verbose = not _verbose
            console.print(f"[dim]Verbose mode: {'ON' if _verbose else 'OFF'}[/dim]\n")
            continue

        if user_input == "/clear":
            history = []
            console.print("[dim]Conversation history cleared.[/dim]\n")
            continue

        if user_input in ("/quit", "/exit", "/q"):
            console.print("[dim]Goodbye![/dim]")
            break

        # ── Run pipeline ──────────────────────────────────────
        console.print()
        with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
            result = orchestrator.run(user_input, history, verbose=_verbose)

        # ── Print answer ──────────────────────────────────────
        console.print(Rule(style="dim"))
        console.print("[bold blue]Assistant:[/bold blue]")
        console.print(Markdown(result["answer"]))

        # ── Print metadata ────────────────────────────────────
        if result["sources"]:
            console.print(f"\n[dim]Sources: {', '.join(result['sources'])}[/dim]")

        if result["pipeline"] == "rag":
            score   = result["critic_score"]
            verdict = result["critic_verdict"]
            color   = "green" if verdict == "PASS" else "yellow"
            console.print(
                f"[dim]Faithfulness: [{color}]{verdict}[/{color}] "
                f"({score:.2f})[/dim]"
            )

        console.print(Rule(style="dim"))
        console.print()

        # ── Update history ────────────────────────────────────
        history.append({"role": "user",      "content": user_input})
        history.append({"role": "assistant", "content": result["answer"]})

        # Keep history bounded to last 10 turns
        if len(history) > 20:
            history = history[-20:]


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent RAG Assistant")
    parser.add_argument("--verbose", action="store_true",
                        help="Show agent pipeline trace")
    parser.add_argument("--ingest", metavar="PATH",
                        help="Ingest a file or folder before starting chat")
    args = parser.parse_args()

    if args.ingest:
        ingest_path(args.ingest)
        console.print()

    chat_loop(verbose=args.verbose)


if __name__ == "__main__":
    main()