# Transaction Pattern Detector

A Python-based system that detects potential structuring patterns in financial transactions using deterministic, rule-based detection and generates analyst-friendly explanations using an LLM.
### How It Works

- **Python Detector (`structuring.py`):** Filters eligible credit transactions, groups them by account, checks individual amounts, minimum transaction count, combined amount, and rolling time window.
- **Structured Evidence:** Contains account ID, transaction IDs, transaction count, total amount, threshold, and time window.
- **LLM Explainer (`llm_explanation.py`):** Sends only structured evidence to the Groq API to generate an analyst-friendly explanation.
- **Important:** The LLM does not receive the raw CSV or make detection decisions. All detection is performed by Python.

## Project Structure

```text
Arun_kumar_assignment/
│
├── config/
│   └── config.json
│
├── data/
│   └── transactions.csv
│
├── detector/
│   ├── __init__.py
│   ├── structuring.py
│   └── test.py
│
├── llm_response/
│   ├── __init__.py
│   └── llm_explanation.py
│
├── output/
│   └── results.json
│
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── DECISIONS.md
```

## Setup and Run

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Arun_kumar_assignment
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Groq API key

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run the application

```bash
python main.py
```

Detection results and LLM explanations are saved in:

```text
output/results.json
```

## Run Tests

```bash
python -m pytest detector/test.py -v
```

The test suite covers valid detection, threshold conditions, rolling-window boundaries, debit exclusion, account separation, and invalid configuration.

