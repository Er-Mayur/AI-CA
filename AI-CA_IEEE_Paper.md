# AI-CA (AICI): An Offline AI-Powered Tax Compliance Platform for Indian Income Tax

**Authors:** Your Name(s)  
**Affiliation:** Your Institution / Organization  
**Email:** your.email@example.com

---

## Abstract  
AI-CA (AICI) is an offline, AI-powered tax compliance system for Indian Income Tax. The platform ingests Form 16, Form 26AS, and AIS PDFs, verifies identity via strict PAN and financial-year matching, extracts structured tax data using multi-method PDF parsing and OCR, computes liabilities under old and new regimes, recommends the optimal regime, and generates downloadable reports. The system runs fully locally using a FastAPI backend, React frontend, MySQL database, and a local Mistral 7B model served via Ollama. This paper presents the architecture, document processing pipeline, verification logic, tax computation engine, AI features, evaluation plan, and limitations.

**Keywords:** tax compliance, document intelligence, OCR, PDF parsing, local LLM, offline AI, FastAPI, MySQL

---

## I. Introduction  
Tax compliance in India requires careful handling of multiple documents, strict identity matching, and complex deduction rules. Manual workflows are error-prone and time-intensive. AI-CA addresses these issues through a deterministic extraction pipeline augmented with local AI fallback, ensuring accurate, private, and offline processing. The system is designed to compute liabilities under both old and new tax regimes and provide actionable recommendations.

---

## II. Problem Statement and Motivation  
The core challenges are:  
1) Reliable extraction of tax-relevant fields from diverse PDF formats,  
2) Strict verification against user identity (PAN) and selected financial year, and  
3) Accurate, explainable tax computation under multiple regimes.  

AI-CA aims to automate these steps while maintaining privacy by avoiding cloud dependencies.

---

## III. Related Work  
AI-CA builds on established tools in PDF parsing and OCR: pdfplumber, pdfminer.six, PyPDF2, and Tesseract OCR with Poppler for scanned documents. The backend uses FastAPI for API routing, and the frontend uses React and Vite. Local LLM inference is provided by Ollama, with Mistral models for AI fallback and advisory responses.

---

## IV. System Overview  
AI-CA is a three-layer system:
- **Frontend**: React + Vite + Tailwind for UI and dashboards.  
- **Backend**: FastAPI routers for authentication, document workflows, tax computation, dashboard aggregation, Q&A, and investments.  
- **Data Layer**: MySQL for local persistence of user records, documents, computations, rules, and chat history.

### Figure 1. System Architecture Diagram  
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
  <defs>
    <style>
      .box { fill: #f7f7f7; stroke: #333; stroke-width: 2; }
      .title { font: 18px sans-serif; font-weight: bold; }
      .label { font: 14px sans-serif; }
      .arrow { stroke: #333; stroke-width: 2; marker-end: url(#arrow); }
    </style>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
      <path d="M0,0 L12,6 L0,12 Z" fill="#333"/>
    </marker>
  </defs>

  <text x="20" y="30" class="title">Figure 1. AI-CA System Architecture</text>

  <rect x="40" y="80" width="220" height="80" class="box"/>
  <text x="60" y="120" class="label">Client: User (Browser)</text>

  <rect x="300" y="80" width="320" height="120" class="box"/>
  <text x="320" y="115" class="label">Frontend (React + Vite + Tailwind)</text>
  <text x="320" y="145" class="label">Pages: Landing, Login, Dashboard, Docs</text>
  <text x="320" y="165" class="label">Tax, Q&amp;A, Benefits</text>

  <rect x="680" y="80" width="460" height="120" class="box"/>
  <text x="700" y="115" class="label">Backend (FastAPI Routers)</text>
  <text x="700" y="145" class="label">Auth, Documents, Tax, Dashboard, Q&amp;A, Investments</text>

  <rect x="300" y="260" width="360" height="220" class="box"/>
  <text x="320" y="290" class="label">Processing &amp; AI</text>
  <text x="320" y="320" class="label">pdf_processor, smart_extractor, text_cleaner</text>
  <text x="320" y="350" class="label">Tesseract OCR, rules_service, tax_calculator</text>
  <text x="320" y="380" class="label">rag_engine, ollama_client (Mistral)</text>

  <rect x="700" y="260" width="360" height="220" class="box"/>
  <text x="720" y="290" class="label">MySQL Database</text>
  <text x="720" y="320" class="label">users, documents, tax_computations</text>
  <text x="720" y="350" class="label">tax_rules, investment_suggestions</text>
  <text x="720" y="380" class="label">activity_history, qna_chats, qna_messages</text>

  <line x1="260" y1="120" x2="300" y2="120" class="arrow"/>
  <line x1="620" y1="120" x2="680" y2="120" class="arrow"/>
  <line x1="500" y1="200" x2="500" y2="260" class="arrow"/>
  <line x1="860" y1="200" x2="860" y2="260" class="arrow"/>
</svg>
```

---

## V. Architecture  
The backend exposes endpoints for registration/login, document upload and verification, tax computation, dashboard summaries, Q&A, and investment suggestions. Document processing, AI fallback, and tax computation are modularized into dedicated utilities.

### Figure 2. Document Processing and Verification Pipeline  
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">
  <defs>
    <style>
      .box { fill: #f7f7f7; stroke: #333; stroke-width: 2; }
      .label { font: 14px sans-serif; }
      .title { font: 18px sans-serif; font-weight: bold; }
      .arrow { stroke: #333; stroke-width: 2; marker-end: url(#arrow); }
    </style>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
      <path d="M0,0 L12,6 L0,12 Z" fill="#333"/>
    </marker>
  </defs>

  <text x="20" y="30" class="title">Figure 2. Document Processing and Verification Pipeline</text>

  <rect x="60" y="80" width="200" height="60" class="box"/>
  <text x="70" y="115" class="label">Upload PDF</text>

  <rect x="320" y="80" width="280" height="60" class="box"/>
  <text x="330" y="115" class="label">Multi-method Extraction</text>

  <rect x="660" y="80" width="220" height="60" class="box"/>
  <text x="670" y="115" class="label">OCR (if scanned)</text>

  <rect x="320" y="180" width="280" height="60" class="box"/>
  <text x="330" y="215" class="label">Normalize Text</text>

  <rect x="320" y="280" width="280" height="60" class="box"/>
  <text x="330" y="315" class="label">Pattern Extraction</text>

  <rect x="320" y="380" width="280" height="60" class="box"/>
  <text x="330" y="415" class="label">Confidence Check</text>

  <rect x="660" y="380" width="220" height="60" class="box"/>
  <text x="670" y="415" class="label">LLM Fallback</text>

  <rect x="320" y="480" width="280" height="60" class="box"/>
  <text x="330" y="515" class="label">Strict PAN/FY Verify</text>

  <rect x="320" y="580" width="280" height="60" class="box"/>
  <text x="330" y="615" class="label">Store / Reject</text>

  <line x1="260" y1="110" x2="320" y2="110" class="arrow"/>
  <line x1="600" y1="110" x2="660" y2="110" class="arrow"/>
  <line x1="460" y1="140" x2="460" y2="180" class="arrow"/>
  <line x1="460" y1="240" x2="460" y2="280" class="arrow"/>
  <line x1="460" y1="340" x2="460" y2="380" class="arrow"/>
  <line x1="600" y1="410" x2="660" y2="410" class="arrow"/>
  <line x1="460" y1="440" x2="460" y2="480" class="arrow"/>
  <line x1="460" y1="540" x2="460" y2="580" class="arrow"/>
</svg>
```

---

## VI. Data Model and Storage  
The MySQL schema includes: `users`, `documents`, `tax_computations`, `tax_rules`, `investment_suggestions`, `activity_history`, `qna_chats`, and `qna_messages`.

### Figure 3. Database ER Diagram  
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="750" viewBox="0 0 1200 750">
  <defs>
    <style>
      .box { fill: #f7f7f7; stroke: #333; stroke-width: 2; }
      .label { font: 14px sans-serif; }
      .title { font: 18px sans-serif; font-weight: bold; }
      .arrow { stroke: #333; stroke-width: 2; marker-end: url(#arrow); }
    </style>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
      <path d="M0,0 L12,6 L0,12 Z" fill="#333"/>
    </marker>
  </defs>

  <text x="20" y="30" class="title">Figure 3. Database ER Diagram (Simplified)</text>

  <rect x="60" y="80" width="200" height="80" class="box"/>
  <text x="80" y="115" class="label">users</text>

  <rect x="320" y="80" width="220" height="80" class="box"/>
  <text x="340" y="115" class="label">documents</text>

  <rect x="600" y="80" width="240" height="80" class="box"/>
  <text x="620" y="115" class="label">tax_computations</text>

  <rect x="320" y="220" width="220" height="80" class="box"/>
  <text x="340" y="255" class="label">investment_suggestions</text>

  <rect x="600" y="220" width="240" height="80" class="box"/>
  <text x="620" y="255" class="label">activity_history</text>

  <rect x="320" y="360" width="220" height="80" class="box"/>
  <text x="340" y="395" class="label">qna_chats</text>

  <rect x="600" y="360" width="240" height="80" class="box"/>
  <text x="620" y="395" class="label">qna_messages</text>

  <rect x="920" y="80" width="200" height="80" class="box"/>
  <text x="940" y="115" class="label">tax_rules</text>

  <line x1="260" y1="120" x2="320" y2="120" class="arrow"/>
  <line x1="260" y1="120" x2="320" y2="260" class="arrow"/>
  <line x1="260" y1="120" x2="320" y2="400" class="arrow"/>
  <line x1="540" y1="120" x2="600" y2="120" class="arrow"/>
  <line x1="540" y1="260" x2="600" y2="260" class="arrow"/>
  <line x1="540" y1="400" x2="600" y2="400" class="arrow"/>
  <line x1="840" y1="120" x2="920" y2="120" class="arrow"/>
</svg>
```

---

## XI. Tables

### Table I. Technology Stack  
| Layer | Component | Technology |
|---|---|---|
| Frontend | UI | React, Vite, Tailwind |
| Backend | API | FastAPI |
| Database | Storage | MySQL |
| AI | Local LLM | Mistral 7B via Ollama |
| PDF Parsing | Text Extraction | pdfplumber, pdfminer.six, PyPDF2 |
| OCR | Image PDFs | Tesseract + Poppler |
| Auth | Security | JWT, bcrypt |

### Table II. Pipeline Metrics (Reported)  
| Stage | Metric | Reported Value |
|---|---|---|
| Text PDF extraction | Latency | < 1 second |
| Scanned PDF OCR | Latency | 10-30 seconds |
| AI verification | Latency | 2-5 seconds |
| PAN extraction | Accuracy | ~99.9% |
| Name matching | Accuracy | 95-98% |
| Doc type detection | Accuracy | ~99% |
| Overall success | Rate | 95-99% |

---

## References  
[1] AI-CA Project README.  
[2] AI-CA Project Summary.  
[3] Ollama. https://ollama.com/  
[4] FastAPI Documentation. https://fastapi.tiangolo.com/  
[5] Mistral AI Documentation. https://docs.mistral.ai/  
[6] pdfplumber. https://pypi.org/project/pdfplumber/  
[7] pdfminer.six. https://pypi.org/project/pdfminer.six/  
[8] PyPDF2. https://pypi.org/project/PyPDF2/  
[9] Tesseract OCR. https://github.com/tesseract-ocr/tesseract  
[10] Poppler. https://poppler.freedesktop.org/  
[11] MySQL. https://www.mysql.com/  
[12] React. https://react.dev/  
[13] Vite. https://vite.dev/  
[14] Tailwind CSS. https://tailwindcss.com/
```

If you want me to create the file for you, run the following command in your terminal:

```bash
cat > /Users/mayur/Projects/AI-CA/AI-CA_IEEE_Paper.md << 'EOF'
[PASTE THE CONTENT ABOVE HERE]
EOF
```
