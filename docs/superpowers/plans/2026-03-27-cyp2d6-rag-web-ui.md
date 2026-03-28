# CYP2D6 RAG Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a clean, conversational React frontend for the CYP2D6 metabolism RAG assistant, including a citation-aware FastAPI backend.

**Architecture:** A React SPA (Vite-powered) communicating via JSON with a FastAPI backend. The backend will wrap the existing RAG logic and provide structured responses (answer, citations, and a status badge).

**Tech Stack:** React (Vite), Vanilla CSS, FastAPI, ChromaDB.

---

### Task 1: Backend - Extend FastAPI for UI Support

**Files:**
- Modify: `deploy_rag/app.py`
- Test: `deploy_rag/test_app.py` (New)

- [ ] **Step 1: Update the QueryResponse model**
Add `citations` and `is_substrate` fields to the response model.
- [ ] **Step 2: Update the /query endpoint**
Modify the logic to extract drug IDs, SMILES, and substrate status from the RAG results.
- [ ] **Step 3: Create a basic test for the new endpoint**
Run: `pytest deploy_rag/test_app.py`
Expected: PASS

### Task 2: Frontend - Scaffold React with Vite

**Files:**
- Create: `frontend/` (Vite project)
- Create: `frontend/src/App.css` (Base styles)

- [ ] **Step 1: Initialize Vite/React**
Run: `npm create vite@latest frontend -- --template react` (Followed by `npm install`)
- [ ] **Step 2: Add base Vanilla CSS**
Set up the font, colors, and layout containers defined in the mockup.
- [ ] **Step 3: Commit**

### Task 3: Frontend - Implementation of Chat Components

**Files:**
- Create: `frontend/src/components/Message.jsx`
- Create: `frontend/src/components/CitationCard.jsx`
- Create: `frontend/src/components/ChatWindow.jsx`

- [ ] **Step 1: Build CitationCard component**
A small clickable card that displays drug metadata.
- [ ] **Step 2: Build Message component**
Handles rendering user vs. assistant bubbles, including the status badge.
- [ ] **Step 3: Build ChatWindow component**
Manages the scrollable message list and the input area.
- [ ] **Step 4: Commit**

### Task 4: Frontend - API Integration & State Management

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Implement fetch logic**
Connect the frontend to the FastAPI `/query` endpoint.
- [ ] **Step 2: Add loading states**
Show a "typing" indicator while the query is in flight.
- [ ] **Step 3: Add medical disclaimer footer**
Finalize the UI with the required safety warning.
- [ ] **Step 4: Commit**

### Task 5: End-to-End Validation

- [ ] **Step 1: Start Backend**
Run: `uvicorn deploy_rag.app:app --reload --port 8000`
- [ ] **Step 2: Start Frontend**
Run: `cd frontend && npm run dev`
- [ ] **Step 3: Verify Query Flow**
Ask "Is Codeine a substrate?" and confirm the "Yes" badge and citations appear.
- [ ] **Step 4: Commit and finalize**
