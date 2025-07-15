# tum-gen-ai-24

## Getting Started

This guide will walk you through setting up the project and running the financial report chat demo.

### Prerequisites

- Python 3.9 or higher
- An OpenAI API key

### 1. Clone the Repository

```bash
git clone https://github.com/Koussay-Khelil/tum-gen-ai-24.git
cd tum-gen-ai-24
```

### 2. Set Up the Environment

Create a virtual environment to manage project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Create a `.env` file in the root of the project and add your OpenAI API key:

```
API_KEY=your_openai_api_key
```

### 5. Run the Chat Demo

Execute the `cli_chat_demo.py` script to start the interactive chat with the financial report agent:

```bash
python excel_ocr/cli_chat_demo.py
```

You can now ask questions about the financial data in `demo_data.xlsx`.
