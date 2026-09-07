# Adaptive Multi-Agent Framework for Automated Research Gap Identification and Scientific Knowledge Synthesis

This is a state-of-the-art research analysis and discovery tool. It leverages a team of cooperative LLM agents managed by a stateful LangGraph execution engine to ingest academic papers, criticize their experimental structures, compare methodologies, and map a landscape of unresolved scientific gaps.

---

## Key Features
- **Multi-Agent Coordination (LangGraph)**: Directs a specialized graph flow spanning paper retrieval, critique analysis, gap identification, and final literature synthesis writing.
- **Relational + Vector Store**: Employs PostgreSQL with `pgvector` to index paper segments alongside traditional relational data like logs and gap taxonomies.
- **Document Segmentation Pipeline**: Uses PyMuPDF heuristics to parse headers and split PDFs into structured context sections.
- **Real-Time Monitoring**: Streams agent execution state steps dynamically using WebSockets.
- **Interconnected Dashboards**: A premium Next.js dashboard featuring citation networks, gap landscapes, and an interactive markdown document editor.

---

## System Architecture Layout
```
ResearchGapAI/
├── backend/            # FastAPI + LangGraph + Celery
│   ├── app/
│   │   ├── agents/     # LangGraph workflows and node tools
│   │   ├── api/        # REST endpoints and WebSocket stream handlers
│   │   ├── core/       # DB session, security, config
│   │   ├── models/     # SQLModel tables (User, Project, Paper, Gap, Log)
│   │   ├── services/   # Paper search, PDF structuring
│   │   └── tasks/      # Celery task definitions
│   └── Dockerfile
├── frontend/           # Next.js App router web app
│   ├── src/
│   │   ├── app/        # Dashboard, projects interfaces
│   │   └── components/ # UI assets and network visualizers
│   └── Dockerfile
├── docker-compose.yml  # Local cluster setup
└── README.md
```

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (if running frontend locally)
- Python 3.11+ (if running backend locally)

### Quick Start with Docker
1. Clone the repository and navigate to the directory:
   ```bash
   cd ResearchGapAI
   ```
2. Copy the template `.env.example` file and configure your API keys:
   ```bash
   cp .env.example .env
   ```
3. Boot the environment cluster:
   ```bash
   docker-compose up --build
   ```
4. Access the interfaces:
   - **Frontend UI**: `http://localhost:3000`
   - **FastAPI Documentation**: `http://localhost:8000/docs`

### Local Development Setup

#### Backend
1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your environment variables (see `.env.example`) and start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install client dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
