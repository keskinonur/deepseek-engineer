# DeepSeek Engineer v2 🐋🦙

## Overview

DeepSeek Engineer v2 is a powerful AI-powered coding assistant that provides an interactive terminal interface for seamless code development. Now supports both **DeepSeek's advanced reasoning models** and **local Ollama models**, offering intelligent file operations, code analysis, and development assistance through natural conversation and function calling.

## 🚀 Latest Update: Multi-Provider Support

**Version 2.1** now supports both cloud and local AI providers:
- **🐋 DeepSeek**: Advanced reasoning models with Chain of Thought capabilities
- **🦙 Ollama**: Local models for privacy, offline work, and cost-free usage
- **Seamless switching** between providers with simple configuration
- **Unified interface** - same powerful features regardless of provider

## Key Features

### 🧠 **AI Capabilities**
- **Elite Software Engineering**: Decades of experience across all programming domains
- **Chain of Thought Reasoning**: Visible thought process (DeepSeek) or efficient processing (Ollama)
- **Code Analysis & Discussion**: Expert-level insights and optimization suggestions
- **Intelligent Problem Solving**: Automatic file reading and context understanding

### 🛠️ **Function Calling Tools**
The AI can automatically execute these operations when needed:

#### `read_file(file_path: str)`
- Read single file content with automatic path normalization
- Built-in error handling for missing or inaccessible files
- **Automatic**: AI can read any file you mention or reference in conversation

#### `read_multiple_files(file_paths: List[str])`
- Batch read multiple files efficiently
- Formatted output with clear file separators

#### `create_file(file_path: str, content: str)`
- Create new files or overwrite existing ones
- Automatic directory creation and safety checks

#### `create_multiple_files(files: List[Dict])`
- Create multiple files in a single operation
- Perfect for scaffolding projects or creating related files

#### `edit_file(file_path: str, original_snippet: str, new_snippet: str)`
- Precise snippet-based file editing
- Safe replacement with exact matching

### 🔄 **Multi-Provider Support**

#### **🐋 DeepSeek (Cloud)**
- Advanced reasoning with visible Chain of Thought
- Latest DeepSeek-R1 model capabilities
- Requires API key and internet connection
- Excellent for complex reasoning tasks

#### **🦙 Ollama (Local)**
- Complete privacy - everything runs locally
- No API costs or internet required (after model download)
- Supports popular models: llama3.2, mistral, codellama, etc.
- Great for sensitive codebases or offline development

### 📁 **File Operations**

#### **Automatic File Reading (Recommended)**
The AI can automatically read files you mention:
```
You> Can you review the main.py file and suggest improvements?
→ AI automatically calls read_file("main.py")

You> Look at src/utils.py and tests/test_utils.py
→ AI automatically calls read_multiple_files(["src/utils.py", "tests/test_utils.py"])
```

#### **Manual Context Addition (Optional)**
For when you want to preload files into conversation context:
- **`/add path/to/file`** - Include single file in conversation context
- **`/add path/to/folder`** - Include entire directory (with smart filtering)

### 🎨 **Rich Terminal Interface**
- **Color-coded feedback** (green for success, red for errors, yellow for warnings)
- **Real-time streaming** with visible reasoning process (DeepSeek)
- **Structured tables** for diff previews
- **Progress indicators** for long operations
- **Provider-aware interface** showing current AI provider

### 🛡️ **Security & Safety**
- **Path normalization** and validation
- **Directory traversal protection**
- **File size limits** (5MB per file)
- **Binary file detection** and exclusion

## Getting Started

### Prerequisites
- **Python 3.11+**: Required for optimal performance
- **Choose your AI provider**:
  - **DeepSeek**: Get API key from [DeepSeek Platform](https://platform.deepseek.com)
  - **Ollama**: Install from [Ollama.ai](https://ollama.ai)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd deepseek-engineer
   ```

2. **Choose your setup method**:

#### Option A: DeepSeek (Cloud) Setup
```bash
# Create .env file for DeepSeek
echo "AI_PROVIDER=deepseek" > .env
echo "DEEPSEEK_API_KEY=your_api_key_here" >> .env
```

#### Option B: Ollama (Local) Setup
```bash
# Install Ollama (if not already installed)
# Visit https://ollama.ai for installation instructions

# Start Ollama service
ollama serve

# Pull a model (in another terminal)
ollama pull qwen3:8b

# Create .env file for Ollama
echo "AI_PROVIDER=ollama" > .env
echo "OLLAMA_MODEL=qwen3:8b" >> .env
echo "OLLAMA_BASE_URL=http://localhost:11434/v1" >> .env
```

3. **Install dependencies** (choose one method):

   #### Using uv (recommended - faster)
   ```bash
   uv venv
   uv run deepseek-eng.py
   ```

   #### Using pip
   ```bash
   pip install -r requirements.txt
   python3 deepseek-eng.py
   ```

### Configuration Options

Create a `.env` file with your preferred settings:

```bash
# AI Provider (required)
AI_PROVIDER=ollama  # or "deepseek"

# DeepSeek Settings (if using DeepSeek)
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_MODEL=deepseek-reasoner

# Ollama Settings (if using Ollama)
OLLAMA_MODEL=llama3.2  # or mistral, codellama, etc.
OLLAMA_BASE_URL=http://localhost:11434/v1
```

## Usage Examples

### **Provider Commands**
```
You> /provider
→ Shows current AI provider and model

You> /ollama
→ Instructions to switch to Ollama

You> /deepseek
→ Instructions to switch to DeepSeek
```

### **Natural Conversation with Automatic File Operations**
```
You> Can you read the main.py file and create a test file for it?

🦙 Ollama thinking...  # or 🐋 DeepSeek thinking...

🤖 Assistant> I'll read the main.py file first to understand its structure.
⚡ Executing 1 function call(s)...
→ read_file
✓ Read file 'main.py'

🔄 Processing results...
Now I'll create comprehensive tests based on the code structure I found.
⚡ Executing 1 function call(s)...
→ create_file
✓ Created/updated file at 'test_main.py'

I've analyzed main.py and created comprehensive tests covering all the main functions...
```

### **Automatic Multi-File Analysis**
```
You> Compare the implementation in utils.py with the tests in test_utils.py

🤖 Assistant> I'll read both files to analyze the implementation and tests.
⚡ Executing 1 function call(s)...
→ read_multiple_files
✓ Read files: utils.py, test_utils.py

🔄 Processing results...
After analyzing both files, I can see several areas where the tests could be improved...
```

## Provider Comparison

| Feature | DeepSeek 🐋 | Ollama 🦙 |
|---------|-------------|-----------|
| **Cost** | Pay per use | Free after model download |
| **Privacy** | Cloud-based | 100% local |
| **Internet** | Required | Not required (after setup) |
| **Reasoning** | Chain of Thought visible | Efficient processing |
| **Models** | DeepSeek-R1, specialized reasoning | llama3.2, mistral, codellama, etc. |
| **Setup** | API key only | Install + model download |
| **Performance** | Optimized for reasoning | Depends on local hardware |

## Supported Ollama Models

**Recommended models with function calling support:**

- **🧠 qwen3:8b** - Latest Qwen model with excellent reasoning (recommended)
- **🔧 devstral:24b** - Specialized coding model by Mistral (large, excellent for complex tasks)
- **💻 qwen2.5-coder:7b** - Code-focused Qwen model (programming specialist)
- **⚡ llama3.2:3b** - Lightweight and fast (resource efficient)
- **🎯 mixtral:8x7b** - Mixture of experts, very capable (advanced reasoning)
- **🌟 mistral-small3.1:latest** - Latest Mistral small model
- **🔥 mistral:7b** - General purpose, good balance
- **📚 qwen2.5:7b** - Previous Qwen generation, solid performance

**🔍 Find more tool-compatible models:** [Ollama Tools Search](https://ollama.com/search?c=tools)

> **Note**: Only models with function calling support can perform file operations. Visit the link above to browse all compatible models in the Ollama library.

### Model Installation
```bash
# List available models
ollama list

# Pull recommended models
ollama pull qwen3:8b               # Latest, excellent reasoning
ollama pull devstral:24b           # Large coding specialist  
ollama pull qwen2.5-coder:7b       # Code-focused
ollama pull llama3.2:3b            # Lightweight option
ollama pull mixtral:8x7b           # Advanced reasoning

# Use in .env file
OLLAMA_MODEL=qwen3:8b
```

**Model Selection Guide:**
- **For general coding**: `qwen3:8b` or `mistral:7b`
- **For specialized coding**: `devstral:24b` or `qwen2.5-coder:7b`
- **For resource-constrained systems**: `llama3.2:3b`
- **For complex reasoning**: `mixtral:8x7b`

**System Requirements:**
- **3B models**: 4GB+ RAM
- **7-8B models**: 8GB+ RAM (recommended)
- **24B models**: 16GB+ RAM
- **8x7B models**: 32GB+ RAM

## Advanced Features

### **Intelligent Context Management**
- **Automatic file detection** from user messages
- **Smart conversation cleanup** to prevent token overflow
- **File content preservation** across conversation history
- **Tool message integration** for complete operation tracking

### **Batch Operations**
```
You> Create a complete Flask API with models, routes, and tests

🤖 Assistant> I'll create a complete Flask API structure for you.
⚡ Executing 1 function call(s)...
→ create_multiple_files
✓ Created 4 files: app.py, models.py, routes.py, test_api.py
```

### **Provider Switching**
```bash
# Switch to Ollama
echo "AI_PROVIDER=ollama" > .env

# Switch to DeepSeek
echo "AI_PROVIDER=deepseek" > .env

# Restart the application to apply changes
```

## Troubleshooting

### **DeepSeek Issues**

**API Key Not Found**
```bash
# Make sure .env file exists with your API key
echo "DEEPSEEK_API_KEY=your_key_here" > .env
echo "AI_PROVIDER=deepseek" >> .env
```

### **Ollama Issues**

**Connection Refused**
```bash
# Make sure Ollama is running
ollama serve

# Check if models are available
ollama list

# Pull the model if needed
ollama pull llama3.2
```

**Model Not Found**
```bash
# List available models
ollama list

# Browse all tool-compatible models online
# Visit: https://ollama.com/search?c=tools

# Pull the specific model
ollama pull your_model_name

# Update .env file
echo "OLLAMA_MODEL=your_model_name" > .env
```

**Performance Issues**
```bash
# Try a smaller model
ollama pull phi3
echo "OLLAMA_MODEL=phi3" > .env

# Or check system resources
htop  # or Task Manager on Windows
```

### **General Issues**

**Import Errors**
```bash
# Install dependencies
uv sync  # or pip install -r requirements.txt
```

**File Permission Errors**
- Ensure you have write permissions in the working directory
- Check file paths are correct and accessible

## Contributing

This project showcases multi-provider AI capabilities with both cloud and local models. Contributions are welcome!

### **Development Setup**
```bash
git clone <repository-url>
cd deepseek-engineer
uv venv
uv sync
```

### **Run with Different Providers**
```bash
# Run with Ollama (local)
AI_PROVIDER=ollama uv run deepseek-eng.py

# Run with DeepSeek (cloud)
AI_PROVIDER=deepseek uv run deepseek-eng.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

> **Note**: This project demonstrates the flexibility of modern AI development - choose cloud power with DeepSeek for advanced reasoning, or local privacy with Ollama for cost-free, offline development. The same powerful interface works with both! 🚀

### Quick Start Commands

```bash
# Ollama Setup (Local & Free)
ollama serve
ollama pull qwen3:8b
echo -e "AI_PROVIDER=ollama\nOLLAMA_MODEL=qwen3:8b" > .env
uv run deepseek-eng.py

# DeepSeek Setup (Cloud & Advanced)
echo -e "AI_PROVIDER=deepseek\nDEEPSEEK_API_KEY=your_key" > .env
uv run deepseek-eng.py
```

Happy coding with your AI assistant of choice! 🤖✨