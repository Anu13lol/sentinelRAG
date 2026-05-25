# SentinelRAG
**Enterprise AI Agent Auditor & Trust Layer**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com) [![Gemini 2.5](https://img.shields.io/badge/Gemini-2.5_Flash-orange.svg)](https://deepmind.google/technologies/gemini/) [![Veea Lobster Trap](https://img.shields.io/badge/Security-Veea_Lobster_Trap-red.svg)](https://github.com/veeainc/lobstertrap)

## The Problem
Enterprise RAG (Retrieval-Augmented Generation) pipelines are fundamentally broken. While companies spend millions deploying AI agents, 78% of these projects stall because they lack a reliable trust layer. Currently, when an AI model confidently provides an incorrect answer (hallucinates) or falls victim to prompt injection, it happens silently. 

## The Solution: SentinelRAG
SentinelRAG is a real-time quality control and security firewall for enterprise AI pipelines. It acts as a "spell-checker for truth," monitoring every AI-generated response, scoring it for factual accuracy, and blocking malicious prompt injections at the network layer before the response reaches the user.


```mermaid
graph TD
    %% Entry Layer
    UserIn([User Query]) --> API[FastAPI Backend]

    %% Retrieval Pipeline
    API --> Ret[MMR Retriever]
    Ret --> Chroma[(ChromaDB)]
    Chroma -->|"Context Chunks"| API

    %% Security Firewall Layer
    API --> LT{Veea Lobster Trap\nProxy :8080}
    LT -->|"Detected Injection"| Block[Block Request & Log]
    
    %% Processing Layer
    LT -->|"Clean Prompt"| Pro[Gemini 2.5 Flash<br/> Reasoning Engine]
    Pro -->|"Draft Answer"| Eval[Evaluation Layer]

    %% Evaluation Layer Split
    Eval --> Heuristics[Regex/Heuristic Engine]
    Eval --> FlashLite[Gemini 2.5 Flash-Lite<br/>LLM-as-a-Judge]
    
    %% Scoring and Audit
    Heuristics --> Scorer[Confidence Scorer]
    FlashLite --> Scorer
    Scorer --> DB[(SQLite Audit Trail)]
    
    %% Final Delivery Output
    Scorer -->|"Verified Answer + XAI"| UserOut([User Output Display])

    %% Styling for better readability
    style LT fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style Block fill:#f8d7da,stroke:#dc3545,stroke-width:2px
```
## Architecture & Tech Stack

SentinelRAG utilizes a multi-model, hardware-proxied architecture designed for low latency and high observability.
|Component            |Technology           |Purpose                                                                                                                    |
|:--------------------|:--------------------|:--------------------------------------------------------------------------------------------------------------------------|
|**Security Proxy**   |Veea Lobster Trap    |P4-style Deep Prompt Inspection (DPI) firewall. Intercepts traffic at `localhost:8080` to block injections and obfuscation.|
|**Reasoning Brain**  |Gemini 2.5 Flash     |Core LLM generation via the native `google-genai` SDK.                                                                     |
|**Evaluation Engine**|Gemini 2.5 Flash-Lite|LLM-as-a-Judge. High-speed, deterministic JSON output for evaluating relevance and faithfulness.                           |
|**Vector Database**  |ChromaDB             |Local vector store utilizing MMR (Maximal Marginal Relevance) for diverse context retrieval.                               |
|**Audit Database**   |SQLite + SQLAlchemy  |Relational logging of all queries, responses, and evaluation reasoning for compliance.                                     |
|**Backend API**      |FastAPI (Python)     |High-performance API orchestration.                                                                                        |

---

## 🛡️ Core Features

### 1. Hardware-Level Guardrails (Veea Lobster Trap)
SentinelRAG routes all outbound LLM traffic through Veea Lobster Trap. This provides sub-millisecond, regex-based security checks without requiring an expensive LLM call.
* **Blocks Prompt Injections:** Catches "ignore previous instructions" and jailbreak attempts.
* **Detects Obfuscation:** Flags encoded or evasive prompts.
* **Zero Code Changes:** Operates as a transparent network proxy.

### 2. Dual-Stage Hallucination Detection
To optimize for latency and API cost, we implemented a two-stage evaluation pipeline:
1. **The Fast Path (Heuristics):** Instant, regex-based verification. If the AI returns a hard data point (e.g., a specific date or dosage number) that does not exist in the source document, it is immediately flagged.
2. **The Deep Path (LLM-as-a-Judge):** If the heuristic check passes, Gemini 2.5 Flash-Lite performs a strict semantic comparison to ensure the AI's claims are fully supported by the retrieved context.

### 3. The Sentinel Trust Score
Every query receives a deterministic confidence score based on our weighted evaluation matrix:

| Metric | Weight | Description |
| :--- | :--- | :--- |
| **Faithfulness** | 60% | Is the answer strictly grounded in the retrieved chunks? |
| **Relevance** | 40% | Did the retriever fetch the correct semantic context for the query? |
| **Hallucination Cap**| N/A | If a hallucination is detected, the total score is hard-capped at `0.3` (FAIL). |

### 4. Explainable AI (XAI) Audit Trail
SentinelRAG doesn't just block bad answers; it explains *why*. Every query is logged to an SQLite database containing:
* The original user prompt.
* The specific document chunks (evidence) used by the LLM.
* The calculated evaluation scores.
* The JSON reasoning string explaining the evaluation outcome.

---

## ⚙️ Local Setup & Installation

### Prerequisites
* Python 3.11+
* Git
* [Veea Lobster Trap static binary](https://github.com/veeainc/lobstertrap)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Anu13lol/sentinelRAG
cd sentinelrag
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a .env file in the root directory:
```GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite:///./sentinelrag.db
VECTOR_DB_PATH=./vector_store
```
### 3. Boot the Security Proxy (Terminal 1)
Start the Lobster Trap proxy, routing traffic to the Google API:
```bash
cd lobstertrap
.\lobstertrap.exe serve --policy configs/default_policy.yaml --listen :8080 --backend [https://generativelanguage.googleapis.com]```
(https://generativelanguage.googleapis.com)
```
### 4. Boot the FastAPI Backend (Terminal 2)
```bash
cd sentinelrag
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
## 📡 API Endpoints
The backend exposes the following REST APIs (view swagger docs at http://localhost:8000/docs):

|Method|Endpoint|Description
|--|--|--|
| POST | `/ingest/upload` |Ingests PDFs/CSVs, chunks text, and stores embeddings in ChromaDB
| POST | `/query/` | The core orchestration loop: Retrieve → Proxy → Generate → Evaluate → Log
| GET | `/audit/logs` | Fetches high-level query history for the dashboard
| GET | `/audit/eval{id}` | Retrieves deep-dive evaluation metrics and XAI reasoning for a specific query
| GET | `/status` | Health check for the FastAPI backend and the Lobster Trap proxy

## 📸 How It Works (Step-by-Step)

**Step 1: Document Ingestion**
Upload enterprise PDFs or CSVs directly to the local vector store. SentinelRAG handles the chunking and embedding automatically.
<img src="./assets/step1_ingest.png" alt="Ingest Documents" width="800">

**Step 2: Real-Time Query & Hallucination Catch**
Ask questions against your documents. In this example, the AI attempts to calculate total revenue but hallucinates the final sum. **Gemini Flash-Lite** catches the math error, drops the Faithfulness score to **0%**, and hard-caps the confidence, flagging the response before it reaches the user.
<img src="./assets/step2_query.png" alt="Query Engine Hallucination Detection" width="800">

**Step 3: Explainable AI (XAI) Audit Trail**
Every query, whether it passes or fails, is logged. Security and compliance teams can review the exact confidence scores, hallucination flags, and the underlying reasoning for every single AI interaction.
<img src="./assets/step3_audit.png" alt="Audit Trail" width="800">

## 🎯 Use Cases (Demo Ready)

 - Healthcare: Upload a drug dosage report. SentinelRAG ensures the AI does not hallucinate critical patient dosages.
 - Legal/Finance: Upload a supplier contract. SentinelRAG verifies that the AI's Summary is faithful to the specific defect rate clauses in the text.
 - Security Red-Teaming: Attempt a prompt injection attack and watch Lobster Trap block the transaction in real-time.
 ---
 *Built for **Transforming Enterprise Through AI Hackathon***
