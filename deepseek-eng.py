#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from textwrap import dedent
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.style import Style
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PromptStyle
import time

# Initialize Rich console and prompt session
console = Console()
prompt_session = PromptSession(
    style=PromptStyle.from_dict(
        {
            "prompt": "#0066ff bold",  # Bright blue prompt
            "completion-menu.completion": "bg:#1e3a8a fg:#ffffff",
            "completion-menu.completion.current": "bg:#3b82f6 fg:#ffffff bold",
        }
    )
)

# --------------------------------------------------------------------------------
# 1. Configure OpenAI client and load environment variables
# --------------------------------------------------------------------------------
load_dotenv()  # Load environment variables from .env file

# Configuration for different AI providers
AI_PROVIDER = os.getenv("AI_PROVIDER", "deepseek").lower()  # deepseek or ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")

# Configure client based on provider
if AI_PROVIDER == "ollama":
    client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",  # Ollama doesn't require a real API key
    )
    model_name = OLLAMA_MODEL
    console.print(f"[bold cyan]🦙 Using Ollama with model: {model_name}[/bold cyan]")
else:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        console.print(
            "[bold red]❌ DEEPSEEK_API_KEY not found in environment![/bold red]"
        )
        console.print(
            "[yellow]Please set your DeepSeek API key in .env file or switch to Ollama[/yellow]"
        )
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    model_name = DEEPSEEK_MODEL
    console.print(f"[bold blue]🧠 Using DeepSeek with model: {model_name}[/bold blue]")


# --------------------------------------------------------------------------------
# 2. Define our schema using Pydantic for type safety
# --------------------------------------------------------------------------------
class FileToCreate(BaseModel):
    path: str
    content: str


class FileToEdit(BaseModel):
    path: str
    original_snippet: str
    new_snippet: str


# --------------------------------------------------------------------------------
# 2.1. Define Function Calling Tools
# --------------------------------------------------------------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a single file from the filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read (relative or absolute)",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_multiple_files",
            "description": "Read the content of multiple files from the filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of file paths to read (relative or absolute)",
                    }
                },
                "required": ["file_paths"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file or overwrite an existing file with the provided content",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path where the file should be created",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file",
                    },
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_multiple_files",
            "description": "Create multiple files at once",
            "parameters": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"},
                            },
                            "required": ["path", "content"],
                        },
                        "description": "Array of files to create with their paths and content",
                    }
                },
                "required": ["files"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit an existing file by replacing a specific snippet with new content",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to edit",
                    },
                    "original_snippet": {
                        "type": "string",
                        "description": "The exact text snippet to find and replace",
                    },
                    "new_snippet": {
                        "type": "string",
                        "description": "The new text to replace the original snippet with",
                    },
                },
                "required": ["file_path", "original_snippet", "new_snippet"],
            },
        },
    },
]

# --------------------------------------------------------------------------------
# 3. System prompt
# --------------------------------------------------------------------------------
system_PROMPT = dedent(
    f"""\
    You are an elite software engineer called DeepSeek Engineer with decades of experience across all programming domains.
    Your expertise spans system design, algorithms, testing, and best practices.
    You provide thoughtful, well-structured solutions while explaining your reasoning.

    Current AI Provider: {AI_PROVIDER.upper()}
    Model: {model_name}

    Core capabilities:
    1. Code Analysis & Discussion
       - Analyze code with expert-level insight
       - Explain complex concepts clearly
       - Suggest optimizations and best practices
       - Debug issues with precision

    2. File Operations (via function calls):
       - read_file: Read a single file's content
       - read_multiple_files: Read multiple files at once
       - create_file: Create or overwrite a single file
       - create_multiple_files: Create multiple files at once
       - edit_file: Make precise edits to existing files using snippet replacement

    Guidelines:
    1. Provide natural, conversational responses explaining your reasoning
    2. Use function calls when you need to read or modify files
    3. For file operations:
       - Always read files first before editing them to understand the context
       - Use precise snippet matching for edits
       - Explain what changes you're making and why
       - Consider the impact of changes on the overall codebase
    4. Follow language-specific best practices
    5. Suggest tests or validation steps when appropriate
    6. Be thorough in your analysis and recommendations

    IMPORTANT: In your thinking process, if you realize that something requires a tool call, cut your thinking short and proceed directly to the tool call. Don't overthink - act efficiently when file operations are needed.

    Remember: You're a senior engineer - be thoughtful, precise, and explain your reasoning clearly.
"""
)

# --------------------------------------------------------------------------------
# 4. Helper functions
# --------------------------------------------------------------------------------


def read_local_file(file_path: str) -> str:
    """Return the text content of a local file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def create_file(path: str, content: str):
    """Create (or overwrite) a file at 'path' with the given 'content'."""
    file_path = Path(path)

    # Security checks
    if any(part.startswith("~") for part in file_path.parts):
        raise ValueError("Home directory references not allowed")
    normalized_path = normalize_path(str(file_path))

    # Validate reasonable file size for operations
    if len(content) > 5_000_000:  # 5MB limit
        raise ValueError("File content exceeds 5MB size limit")

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    console.print(
        f"[bold blue]✓[/bold blue] Created/updated file at '[bright_cyan]{file_path}[/bright_cyan]'"
    )


def show_diff_table(files_to_edit: List[FileToEdit]) -> None:
    if not files_to_edit:
        return

    table = Table(
        title="📝 Proposed Edits",
        show_header=True,
        header_style="bold bright_blue",
        show_lines=True,
        border_style="blue",
    )
    table.add_column("File Path", style="bright_cyan", no_wrap=True)
    table.add_column("Original", style="red dim")
    table.add_column("New", style="bright_green")

    for edit in files_to_edit:
        table.add_row(edit.path, edit.original_snippet, edit.new_snippet)

    console.print(table)


def apply_diff_edit(path: str, original_snippet: str, new_snippet: str):
    """Reads the file at 'path', replaces the first occurrence of 'original_snippet' with 'new_snippet', then overwrites."""
    try:
        content = read_local_file(path)

        # Verify we're replacing the exact intended occurrence
        occurrences = content.count(original_snippet)
        if occurrences == 0:
            raise ValueError("Original snippet not found")
        if occurrences > 1:
            console.print(
                f"[bold yellow]⚠ Multiple matches ({occurrences}) found - requiring line numbers for safety[/bold yellow]"
            )
            console.print(
                "[dim]Use format:\n--- original.py (lines X-Y)\n+++ modified.py[/dim]"
            )
            raise ValueError(f"Ambiguous edit: {occurrences} matches")

        updated_content = content.replace(original_snippet, new_snippet, 1)
        create_file(path, updated_content)
        console.print(
            f"[bold blue]✓[/bold blue] Applied diff edit to '[bright_cyan]{path}[/bright_cyan]'"
        )

    except FileNotFoundError:
        console.print(
            f"[bold red]✗[/bold red] File not found for diff editing: '[bright_cyan]{path}[/bright_cyan]'"
        )
    except ValueError as e:
        console.print(
            f"[bold yellow]⚠[/bold yellow] {str(e)} in '[bright_cyan]{path}[/bright_cyan]'. No changes made."
        )
        console.print("\n[bold blue]Expected snippet:[/bold blue]")
        console.print(
            Panel(
                original_snippet,
                title="Expected",
                border_style="blue",
                title_align="left",
            )
        )
        console.print("\n[bold blue]Actual file content:[/bold blue]")
        console.print(
            Panel(content, title="Actual", border_style="yellow", title_align="left")
        )


def try_handle_add_command(user_input: str) -> bool:
    prefix = "/add "
    if user_input.strip().lower().startswith(prefix):
        path_to_add = user_input[len(prefix) :].strip()
        try:
            normalized_path = normalize_path(path_to_add)
            if os.path.isdir(normalized_path):
                # Handle entire directory
                add_directory_to_conversation(normalized_path)
            else:
                # Handle a single file as before
                content = read_local_file(normalized_path)
                conversation_history.append(
                    {
                        "role": "system",
                        "content": f"Content of file '{normalized_path}':\n\n{content}",
                    }
                )
                console.print(
                    f"[bold blue]✓[/bold blue] Added file '[bright_cyan]{normalized_path}[/bright_cyan]' to conversation.\n"
                )
        except OSError as e:
            console.print(
                f"[bold red]✗[/bold red] Could not add path '[bright_cyan]{path_to_add}[/bright_cyan]': {e}\n"
            )
        return True
    return False


def try_handle_provider_command(user_input: str) -> bool:
    """Handle commands to switch AI provider"""
    if user_input.strip().lower() in ["/ollama", "/deepseek", "/provider"]:
        if user_input.strip().lower() == "/provider":
            console.print(
                f"\n[bold blue]Current provider:[/bold blue] {AI_PROVIDER.upper()}"
            )
            console.print(f"[bold blue]Current model:[/bold blue] {model_name}")
            console.print("\n[bold yellow]Available commands:[/bold yellow]")
            console.print(
                "  [cyan]/ollama[/cyan] - Switch to Ollama (requires restart)"
            )
            console.print(
                "  [cyan]/deepseek[/cyan] - Switch to DeepSeek (requires restart)"
            )
            console.print(
                "\n[dim]To switch providers, update AI_PROVIDER in your .env file[/dim]"
            )
        else:
            provider = (
                "ollama" if user_input.strip().lower() == "/ollama" else "deepseek"
            )
            console.print(
                f"\n[bold yellow]To switch to {provider.upper()}:[/bold yellow]"
            )
            console.print(f"1. Update your .env file: AI_PROVIDER={provider}")
            if provider == "ollama":
                console.print("2. Make sure Ollama is running: ollama serve")
                console.print("3. Pull a model if needed: ollama pull llama3.2")
            console.print("4. Restart the application")
        return True
    return False


def add_directory_to_conversation(directory_path: str):
    with console.status(
        "[bold bright_blue]🔍 Scanning directory...[/bold bright_blue]"
    ) as status:
        excluded_files = {
            # Python specific
            ".DS_Store",
            "Thumbs.db",
            ".gitignore",
            ".python-version",
            "uv.lock",
            ".uv",
            "uvenv",
            ".uvenv",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            ".coverage",
            ".mypy_cache",
            # Node.js / Web specific
            "node_modules",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            ".next",
            ".nuxt",
            "dist",
            "build",
            ".cache",
            ".parcel-cache",
            ".turbo",
            ".vercel",
            ".output",
            ".contentlayer",
            # Build outputs
            "out",
            "coverage",
            ".nyc_output",
            "storybook-static",
            # Environment and config
            ".env",
            ".env.local",
            ".env.development",
            ".env.production",
            # Misc
            ".git",
            ".svn",
            ".hg",
            "CVS",
        }
        excluded_extensions = {
            # Binary and media files
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".ico",
            ".svg",
            ".webp",
            ".avif",
            ".mp4",
            ".webm",
            ".mov",
            ".mp3",
            ".wav",
            ".ogg",
            ".zip",
            ".tar",
            ".gz",
            ".7z",
            ".rar",
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".bin",
            # Documents
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            # Python specific
            ".pyc",
            ".pyo",
            ".pyd",
            ".egg",
            ".whl",
            # UV specific
            ".uv",
            ".uvenv",
            # Database and logs
            ".db",
            ".sqlite",
            ".sqlite3",
            ".log",
            # IDE specific
            ".idea",
            ".vscode",
            # Web specific
            ".map",
            ".chunk.js",
            ".chunk.css",
            ".min.js",
            ".min.css",
            ".bundle.js",
            ".bundle.css",
            # Cache and temp files
            ".cache",
            ".tmp",
            ".temp",
            # Font files
            ".ttf",
            ".otf",
            ".woff",
            ".woff2",
            ".eot",
        }
        skipped_files = []
        added_files = []
        total_files_processed = 0
        max_files = 1000  # Reasonable limit for files to process
        max_file_size = 5_000_000  # 5MB limit

        for root, dirs, files in os.walk(directory_path):
            if total_files_processed >= max_files:
                console.print(
                    f"[bold yellow]⚠[/bold yellow] Reached maximum file limit ({max_files})"
                )
                break

            status.update(f"[bold bright_blue]🔍 Scanning {root}...[/bold bright_blue]")
            # Skip hidden directories and excluded directories
            dirs[:] = [
                d for d in dirs if not d.startswith(".") and d not in excluded_files
            ]

            for file in files:
                if total_files_processed >= max_files:
                    break

                if file.startswith(".") or file in excluded_files:
                    skipped_files.append(os.path.join(root, file))
                    continue

                _, ext = os.path.splitext(file)
                if ext.lower() in excluded_extensions:
                    skipped_files.append(os.path.join(root, file))
                    continue

                full_path = os.path.join(root, file)

                try:
                    # Check file size before processing
                    if os.path.getsize(full_path) > max_file_size:
                        skipped_files.append(f"{full_path} (exceeds size limit)")
                        continue

                    # Check if it's binary
                    if is_binary_file(full_path):
                        skipped_files.append(full_path)
                        continue

                    normalized_path = normalize_path(full_path)
                    content = read_local_file(normalized_path)
                    conversation_history.append(
                        {
                            "role": "system",
                            "content": f"Content of file '{normalized_path}':\n\n{content}",
                        }
                    )
                    added_files.append(normalized_path)
                    total_files_processed += 1

                except OSError:
                    skipped_files.append(full_path)

        console.print(
            f"[bold blue]✓[/bold blue] Added folder '[bright_cyan]{directory_path}[/bright_cyan]' to conversation."
        )
        if added_files:
            console.print(
                f"\n[bold bright_blue]📁 Added files:[/bold bright_blue] [dim]({len(added_files)} of {total_files_processed})[/dim]"
            )
            for f in added_files:
                console.print(f"  [bright_cyan]📄 {f}[/bright_cyan]")
        if skipped_files:
            console.print(
                f"\n[bold yellow]⏭ Skipped files:[/bold yellow] [dim]({len(skipped_files)})[/dim]"
            )
            for f in skipped_files[:10]:  # Show only first 10 to avoid clutter
                console.print(f"  [yellow dim]⚠ {f}[/yellow dim]")
            if len(skipped_files) > 10:
                console.print(f"  [dim]... and {len(skipped_files) - 10} more[/dim]")
        console.print()


def is_binary_file(file_path: str, peek_size: int = 1024) -> bool:
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(peek_size)
        # If there is a null byte in the sample, treat it as binary
        if b"\0" in chunk:
            return True
        return False
    except Exception:
        # If we fail to read, just treat it as binary to be safe
        return True


def ensure_file_in_context(file_path: str) -> bool:
    try:
        normalized_path = normalize_path(file_path)
        content = read_local_file(normalized_path)
        file_marker = f"Content of file '{normalized_path}'"
        if not any(file_marker in msg["content"] for msg in conversation_history):
            conversation_history.append(
                {"role": "system", "content": f"{file_marker}:\n\n{content}"}
            )
        return True
    except OSError:
        console.print(
            f"[bold red]✗[/bold red] Could not read file '[bright_cyan]{file_path}[/bright_cyan]' for editing context"
        )
        return False


def normalize_path(path_str: str) -> str:
    """Return a canonical, absolute version of the path with security checks."""
    path = Path(path_str).resolve()

    # Prevent directory traversal attacks
    if ".." in path.parts:
        raise ValueError(
            f"Invalid path: {path_str} contains parent directory references"
        )

    return str(path)


# --------------------------------------------------------------------------------
# 5. Conversation state and model support detection
# --------------------------------------------------------------------------------


def model_supports_tools() -> bool:
    """Check if the current model supports function calling/tools"""
    if AI_PROVIDER == "deepseek":
        return True  # DeepSeek models support function calling

    # Ollama models that support function calling with specific recommended versions
    tools_supported_models = {
        # Recommended models with specific sizes
        "qwen3:8b",
        "qwen3",
        "devstral:24b",
        "devstral",
        "qwen2.5-coder:7b",
        "qwen2.5-coder",
        "llama3.2:3b",
        "llama3.2",
        "mixtral:8x7b",
        "mixtral",
        "mistral-small3.1:latest",
        "mistral-small3.1",
        "mistral-small",
        "mistral:7b",
        "mistral",
        "qwen2.5:7b",
        "qwen2.5",
        # Legacy support for other common models
        "qwen2",
        "qwen",
        "llama3.1",
        "llama3",
        "llama2",
        "codellama",
        "phi3",
        "gemma2",
        "llava",
        "bakllava",
    }

    # Check if current model matches any supported model
    # Handle both "model:tag" and "model" formats
    model_to_check = model_name.lower()
    base_model = model_to_check.split(":")[0]  # Remove tag if present

    return (
        model_to_check in tools_supported_models or base_model in tools_supported_models
    )


conversation_history = [{"role": "system", "content": system_PROMPT}]

# --------------------------------------------------------------------------------
# 6. OpenAI API interaction with streaming
# --------------------------------------------------------------------------------


def execute_function_call_dict(tool_call_dict) -> str:
    """Execute a function call from a dictionary format and return the result as a string."""
    try:
        function_name = tool_call_dict["function"]["name"]
        arguments = json.loads(tool_call_dict["function"]["arguments"])

        if function_name == "read_file":
            file_path = arguments["file_path"]
            normalized_path = normalize_path(file_path)
            content = read_local_file(normalized_path)
            return f"Content of file '{normalized_path}':\n\n{content}"

        elif function_name == "read_multiple_files":
            file_paths = arguments["file_paths"]
            results = []
            for file_path in file_paths:
                try:
                    normalized_path = normalize_path(file_path)
                    content = read_local_file(normalized_path)
                    results.append(f"Content of file '{normalized_path}':\n\n{content}")
                except OSError as e:
                    results.append(f"Error reading '{file_path}': {e}")
            return "\n\n" + "=" * 50 + "\n\n".join(results)

        elif function_name == "create_file":
            file_path = arguments["file_path"]
            content = arguments["content"]
            create_file(file_path, content)
            return f"Successfully created file '{file_path}'"

        elif function_name == "create_multiple_files":
            files = arguments["files"]
            created_files = []
            for file_info in files:
                create_file(file_info["path"], file_info["content"])
                created_files.append(file_info["path"])
            return f"Successfully created {len(created_files)} files: {', '.join(created_files)}"

        elif function_name == "edit_file":
            file_path = arguments["file_path"]
            original_snippet = arguments["original_snippet"]
            new_snippet = arguments["new_snippet"]

            # Ensure file is in context first
            if not ensure_file_in_context(file_path):
                return f"Error: Could not read file '{file_path}' for editing"

            apply_diff_edit(file_path, original_snippet, new_snippet)
            return f"Successfully edited file '{file_path}'"

        else:
            return f"Unknown function: {function_name}"

    except Exception as e:
        return f"Error executing {function_name}: {str(e)}"


def execute_function_call(tool_call) -> str:
    """Execute a function call and return the result as a string."""
    try:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "read_file":
            file_path = arguments["file_path"]
            normalized_path = normalize_path(file_path)
            content = read_local_file(normalized_path)
            return f"Content of file '{normalized_path}':\n\n{content}"

        elif function_name == "read_multiple_files":
            file_paths = arguments["file_paths"]
            results = []
            for file_path in file_paths:
                try:
                    normalized_path = normalize_path(file_path)
                    content = read_local_file(normalized_path)
                    results.append(f"Content of file '{normalized_path}':\n\n{content}")
                except OSError as e:
                    results.append(f"Error reading '{file_path}': {e}")
            return "\n\n" + "=" * 50 + "\n\n".join(results)

        elif function_name == "create_file":
            file_path = arguments["file_path"]
            content = arguments["content"]
            create_file(file_path, content)
            return f"Successfully created file '{file_path}'"

        elif function_name == "create_multiple_files":
            files = arguments["files"]
            created_files = []
            for file_info in files:
                create_file(file_info["path"], file_info["content"])
                created_files.append(file_info["path"])
            return f"Successfully created {len(created_files)} files: {', '.join(created_files)}"

        elif function_name == "edit_file":
            file_path = arguments["file_path"]
            original_snippet = arguments["original_snippet"]
            new_snippet = arguments["new_snippet"]

            # Ensure file is in context first
            if not ensure_file_in_context(file_path):
                return f"Error: Could not read file '{file_path}' for editing"

            apply_diff_edit(file_path, original_snippet, new_snippet)
            return f"Successfully edited file '{file_path}'"

        else:
            return f"Unknown function: {function_name}"

    except Exception as e:
        return f"Error executing {function_name}: {str(e)}"


def trim_conversation_history():
    """Trim conversation history to prevent token limit issues while preserving tool call sequences"""
    if len(conversation_history) <= 20:  # Don't trim if conversation is still small
        return

    # Always keep the system prompt
    system_msgs = [msg for msg in conversation_history if msg["role"] == "system"]
    other_msgs = [msg for msg in conversation_history if msg["role"] != "system"]

    # Keep only the last 15 messages to prevent token overflow
    if len(other_msgs) > 15:
        other_msgs = other_msgs[-15:]

    # Rebuild conversation history
    conversation_history.clear()
    conversation_history.extend(system_msgs + other_msgs)


def stream_openai_response(user_message: str):
    # Add the user message to conversation history
    conversation_history.append({"role": "user", "content": user_message})

    # Trim conversation history if it's getting too long
    trim_conversation_history()

    # Define provider info upfront for error handling
    provider_icon = "🦙" if AI_PROVIDER == "ollama" else "🐋"
    provider_name = "Ollama" if AI_PROVIDER == "ollama" else "DeepSeek"

    try:
        # Prepare arguments for the API call
        api_args = {
            "model": model_name,
            "messages": conversation_history,
            "stream": True,
        }

        # Check if model supports tools (function calling)
        # Some Ollama models don't support function calling
        if model_supports_tools():
            api_args["tools"] = tools
        else:
            console.print(
                f"[bold yellow]⚠ Model '{model_name}' doesn't support function calling. Using chat-only mode.[/bold yellow]"
            )

        # Add max_completion_tokens only for DeepSeek (some Ollama models might not support it)
        if AI_PROVIDER == "deepseek":
            api_args["max_completion_tokens"] = 64000

        stream = client.chat.completions.create(**api_args)
        console.print(
            f"\n[bold bright_blue]{provider_icon} {provider_name} thinking...[/bold bright_blue]"
        )

        reasoning_started = False
        reasoning_content = ""
        final_content = ""
        tool_calls = []
        supports_tools = model_supports_tools()

        for chunk in stream:
            # Handle reasoning content if available (mainly for DeepSeek)
            if (
                hasattr(chunk.choices[0].delta, "reasoning_content")
                and chunk.choices[0].delta.reasoning_content
            ):
                if not reasoning_started:
                    console.print("\n[bold blue]💭 Reasoning:[/bold blue]")
                    reasoning_started = True
                console.print(chunk.choices[0].delta.reasoning_content, end="")
                reasoning_content += chunk.choices[0].delta.reasoning_content
            elif chunk.choices[0].delta.content:
                if reasoning_started:
                    console.print("\n")  # Add spacing after reasoning
                    console.print(
                        f"\n[bold bright_blue]🤖 Assistant>[/bold bright_blue] ", end=""
                    )
                    reasoning_started = False
                final_content += chunk.choices[0].delta.content
                console.print(chunk.choices[0].delta.content, end="")
            elif supports_tools and chunk.choices[0].delta.tool_calls:
                # Handle tool calls only if model supports them
                for tool_call_delta in chunk.choices[0].delta.tool_calls:
                    if tool_call_delta.index is not None:
                        # Ensure we have enough tool_calls
                        while len(tool_calls) <= tool_call_delta.index:
                            tool_calls.append(
                                {
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            )

                        if tool_call_delta.id:
                            tool_calls[tool_call_delta.index]["id"] = tool_call_delta.id
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_calls[tool_call_delta.index]["function"][
                                    "name"
                                ] += tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                tool_calls[tool_call_delta.index]["function"][
                                    "arguments"
                                ] += tool_call_delta.function.arguments

        console.print()  # New line after streaming

        # Store the assistant's response in conversation history
        assistant_message = {
            "role": "assistant",
            "content": final_content if final_content else None,
        }

        if supports_tools and tool_calls:
            # Convert our tool_calls format to the expected format
            formatted_tool_calls = []
            for i, tc in enumerate(tool_calls):
                if tc["function"]["name"]:  # Only add if we have a function name
                    # Ensure we have a valid tool call ID
                    tool_id = (
                        tc["id"] if tc["id"] else f"call_{i}_{int(time.time() * 1000)}"
                    )

                    formatted_tool_calls.append(
                        {
                            "id": tool_id,
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            },
                        }
                    )

            if formatted_tool_calls:
                # Important: When there are tool calls, content should be None or empty
                if not final_content:
                    assistant_message["content"] = None

                assistant_message["tool_calls"] = formatted_tool_calls
                conversation_history.append(assistant_message)

                # Execute tool calls and add results immediately
                console.print(
                    f"\n[bold bright_cyan]⚡ Executing {len(formatted_tool_calls)} function call(s)...[/bold bright_cyan]"
                )
                for tool_call in formatted_tool_calls:
                    console.print(
                        f"[bright_blue]→ {tool_call['function']['name']}[/bright_blue]"
                    )

                    try:
                        result = execute_function_call_dict(tool_call)

                        # Add tool result to conversation immediately
                        tool_response = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result,
                        }
                        conversation_history.append(tool_response)
                    except Exception as e:
                        console.print(
                            f"[red]Error executing {tool_call['function']['name']}: {e}[/red]"
                        )
                        # Still need to add a tool response even on error
                        conversation_history.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": f"Error: {str(e)}",
                            }
                        )

                # Get follow-up response after tool execution
                console.print(
                    f"\n[bold bright_blue]🔄 Processing results...[/bold bright_blue]"
                )

                follow_up_api_args = {
                    "model": model_name,
                    "messages": conversation_history,
                    "stream": True,
                }

                # Only add tools if model supports them
                if supports_tools:
                    follow_up_api_args["tools"] = tools

                if AI_PROVIDER == "deepseek":
                    follow_up_api_args["max_completion_tokens"] = 64000

                follow_up_stream = client.chat.completions.create(**follow_up_api_args)

                follow_up_content = ""
                reasoning_started = False

                for chunk in follow_up_stream:
                    # Handle reasoning content if available
                    if (
                        hasattr(chunk.choices[0].delta, "reasoning_content")
                        and chunk.choices[0].delta.reasoning_content
                    ):
                        if not reasoning_started:
                            console.print("\n[bold blue]💭 Reasoning:[/bold blue]")
                            reasoning_started = True
                        console.print(chunk.choices[0].delta.reasoning_content, end="")
                    elif chunk.choices[0].delta.content:
                        if reasoning_started:
                            console.print("\n")
                            console.print(
                                f"\n[bold bright_blue]🤖 Assistant>[/bold bright_blue] ",
                                end="",
                            )
                            reasoning_started = False
                        follow_up_content += chunk.choices[0].delta.content
                        console.print(chunk.choices[0].delta.content, end="")

                console.print()

                # Store follow-up response
                conversation_history.append(
                    {"role": "assistant", "content": follow_up_content}
                )
        else:
            # No tool calls, just store the regular response
            conversation_history.append(assistant_message)

        return {"success": True}

    except Exception as e:
        error_msg = f"{provider_name} API error: {str(e)}"
        console.print(f"\n[bold red]❌ {error_msg}[/bold red]")

        # Provide helpful error messages for common issues
        if AI_PROVIDER == "ollama":
            if "Connection" in str(e) or "refused" in str(e):
                console.print("\n[bold yellow]💡 Troubleshooting tips:[/bold yellow]")
                console.print(
                    "1. Make sure Ollama is running: [cyan]ollama serve[/cyan]"
                )
                console.print(
                    "2. Check if the model is available: [cyan]ollama list[/cyan]"
                )
                console.print(
                    f"3. Pull the model if needed: [cyan]ollama pull {OLLAMA_MODEL}[/cyan]"
                )
                console.print(f"4. Verify Ollama URL: [cyan]{OLLAMA_BASE_URL}[/cyan]")
            elif "does not support tools" in str(e):
                console.print(
                    "\n[bold yellow]💡 Model compatibility issue:[/bold yellow]"
                )
                console.print(
                    f"The model '{model_name}' doesn't support function calling."
                )
                console.print(
                    "\n[bold cyan]🦙 Recommended Ollama models with function calling:[/bold cyan]"
                )
                console.print(
                    "• [green]qwen3:8b[/green] - Latest Qwen model, excellent reasoning (recommended)"
                )
                console.print(
                    "• [green]devstral:24b[/green] - Specialized coding model by Mistral"
                )
                console.print(
                    "• [green]qwen2.5-coder:7b[/green] - Code-focused Qwen model"
                )
                console.print("• [green]llama3.2:3b[/green] - Lightweight and fast")
                console.print(
                    "• [green]mixtral:8x7b[/green] - Mixture of experts, very capable"
                )
                console.print(
                    "• [green]mistral:7b[/green] - General purpose, good balance"
                )
                console.print(
                    f"\n[bold blue]Browse all tool-compatible models:[/bold blue] [cyan]https://ollama.com/search?c=tools[/cyan]"
                )
                console.print("\n[bold blue]To switch models:[/bold blue]")
                console.print(
                    "1. Pull a supported model: [cyan]ollama pull qwen3:8b[/cyan]"
                )
                console.print(
                    "2. Update your .env file: [cyan]OLLAMA_MODEL=qwen3:8b[/cyan]"
                )
                console.print("3. Restart the application")

        return {"error": error_msg}


# --------------------------------------------------------------------------------
# 7. Main interactive loop
# --------------------------------------------------------------------------------


def main():
    # Create a beautiful gradient-style welcome panel
    provider_emoji = "🦙" if AI_PROVIDER == "ollama" else "🐋"
    provider_name = "Ollama" if AI_PROVIDER == "ollama" else "DeepSeek"

    welcome_text = f"""[bold bright_blue]{provider_emoji} DeepSeek Engineer[/bold bright_blue] [bright_cyan]with {provider_name}[/bright_cyan]
[dim blue]Powered by {model_name} with Function Calling[/dim blue]"""

    console.print(
        Panel.fit(
            welcome_text,
            border_style="bright_blue",
            padding=(1, 2),
            title="[bold bright_cyan]🤖 AI Code Assistant[/bold bright_cyan]",
            title_align="center",
        )
    )

    # Create an elegant instruction panel
    instructions = f"""[bold bright_blue]📁 File Operations:[/bold bright_blue]
  • [bright_cyan]/add path/to/file[/bright_cyan] - Include a single file in conversation
  • [bright_cyan]/add path/to/folder[/bright_cyan] - Include all files in a folder
  • [dim]The AI can automatically read and create files using function calls[/dim]

[bold bright_blue]🔧 Provider Commands:[/bold bright_blue]
  • [bright_cyan]/provider[/bright_cyan] - Show current provider and model info
  • [bright_cyan]/ollama[/bright_cyan] - Instructions to switch to Ollama
  • [bright_cyan]/deepseek[/bright_cyan] - Instructions to switch to DeepSeek

[bold bright_blue]🎯 Commands:[/bold bright_blue]
  • [bright_cyan]exit[/bright_cyan] or [bright_cyan]quit[/bright_cyan] - End the session
  • Just ask naturally - the AI will handle file operations automatically!

[bold blue]Current Setup:[/bold blue] {provider_name} ({model_name})"""

    console.print(
        Panel(
            instructions,
            border_style="blue",
            padding=(1, 2),
            title="[bold blue]💡 How to Use[/bold blue]",
            title_align="left",
        )
    )

    # Show provider-specific startup info
    if AI_PROVIDER == "ollama":
        console.print(
            Panel(
                "[bold cyan]🦙 Ollama Setup:[/bold cyan]\n"
                f"• Base URL: {OLLAMA_BASE_URL}\n"
                f"• Model: {OLLAMA_MODEL}\n"
                "• Make sure Ollama is running with: [cyan]ollama serve[/cyan]\n"
                f"• Pull model if needed: [cyan]ollama pull {OLLAMA_MODEL}[/cyan]\n"
                "• Browse tool-compatible models: [cyan]https://ollama.com/search?c=tools[/cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    console.print()

    while True:
        try:
            user_input = prompt_session.prompt("🔵 You> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold yellow]👋 Exiting gracefully...[/bold yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            console.print(
                "[bold bright_blue]👋 Goodbye! Happy coding![/bold bright_blue]"
            )
            break

        if try_handle_add_command(user_input):
            continue

        if try_handle_provider_command(user_input):
            continue

        response_data = stream_openai_response(user_input)

        if response_data.get("error"):
            console.print(f"[bold red]❌ Error: {response_data['error']}[/bold red]")

    console.print(
        f"[bold blue]✨ Session finished. Thank you for using DeepSeek Engineer with {provider_name}![/bold blue]"
    )


if __name__ == "__main__":
    main()
