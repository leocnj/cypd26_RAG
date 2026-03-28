# CYP2D6 RAG Web UI Design Specification

**Date:** 2026-03-27
**Status:** Approved
**Topic:** Adding a conversational Web UI for the CYP2D6 pharmacogenomics RAG system.

---

## 1. Overview
The goal of this project is to provide a user-friendly web interface for general and medical users to interact with the CYP2D6 RAG (Retrieval-Augmented Generation) system. Users can ask natural language questions about drug metabolism, and the system will provide evidence-based answers using data from ChromaDB.

## 2. User Experience (UX)
- **Persona:** General/Medical users.
- **Tone:** Authoritative, helpful, and trustworthy.
- **Interaction Style:** Conversational Chat (ChatGPT-like).
- **Key Features:**
    - High-level summaries (Yes/No substrate status).
    - Simplified explanations of complex metabolic pathways.
    - Clickable citation cards linking to source data (PubChem, DrugBank, etc.).

## 3. Visual Design
- **Theme:** Clean, modern, "Medical Assistant" aesthetic.
- **Colors:** Professional blues (#007aff, #0056b3), soft backgrounds (#f0f2f5), and clear status badges (green for substrates, red for non-substrates).
- **Components:**
    - **Header:** Title with medical iconography.
    - **Chat Window:** Threaded messages with distinct styles for User and Assistant.
    - **Status Badges:** Instant visual confirmation of CYP2D6 substrate status.
    - **Citation Cards:** Small, unobtrusive blocks at the bottom of assistant messages showing the retrieved SMILES and Drug IDs.
    - **Floating Input:** A centered, rounded search bar for continuous interaction.

## 4. Technical Architecture
- **Frontend (SPA):** 
    - **Framework:** React (Vite-powered).
    - **Styling:** Vanilla CSS (for maximum flexibility and lightweight footprint).
    - **State Management:** React `useState`/`useEffect` for chat history and loading states.
- **Backend (API):**
    - **Framework:** FastAPI (extension of existing `deploy_rag/app.py`).
    - **Endpoint:** `POST /query` receiving `{ "query": "drug name" }`.
    - **Orchestration:** Interfaces with the existing ChromaDB collection and the RAG logic defined in `04_cli_agent.py`.
- **Data Flow:**
    1. User enters query -> React Sends JSON.
    2. FastAPI receives query -> Triggers RAG Engine.
    3. RAG Engine -> Queries ChromaDB -> LLM Generates Answer -> Bundles Metadata.
    4. FastAPI -> Returns JSON with `answer`, `status_badge`, and `citations`.
    5. React -> Updates UI with "typing" animation and then the final response.

## 5. Directory Structure
```text
/Users/leichen/dev/Github/cypd26_RAG/
├── frontend/               # New React project
│   ├── src/
│   │   ├── components/     # ChatWindow.jsx, Message.jsx, CitationCard.jsx
│   │   ├── App.jsx          # Main layout & state logic
│   │   └── App.css         # All styles (Vanilla CSS)
│   ├── index.html
│   └── package.json
└── deploy_rag/
    └── app.py              # API logic (to be updated)
```

## 6. Security & Safety
- **No PII:** The system should not store or request personal patient data.
- **Medical Disclaimer:** A footer note must state that the tool is for informational purposes only.

## 7. Future Considerations
- Streaming responses for better perceived performance.
- Mobile-responsive layout for on-the-go medical professionals.
- "Drug Card" pop-ups for deeper scientific detail (SMILES, ECFP4).
