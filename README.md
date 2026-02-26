# AI-CA Individual — MVP (FastAPI + React.js)

Features:
- Register/Login (JWT)
- Upload 1) Form 16 2) Form 26AS 3) AIS (PDFs)
- Auto-parse (heuristic) salary/interest/dividend/tds from PDFs
- Tax engine for FY 2024-25 (AY 2025-26): Old vs New + best regime + refund/payable
- Dashboard with charts (Recharts) + Parsed JSON panel
- QnA placeholder endpoint (plug llama.cpp / OpenAI later)

## Run Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # edit secrets if needed
python aica_database_initilization.py
uvicorn app.main:app --reload --port 8000
```

## Run Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev  # http://localhost:3000
```

Login/Register on `/` then open `/dashboard`. Upload PDF(s) and see the computed summary + chart.

> NOTE: Parsers are heuristic and minimal. For production accuracy, add template-based extractors for your specific Form 16/AIS formats and 26AS tables, or integrate OCR where necessary.

## Where to integrate your real AI:
- Backend: `POST /qna` in `main.py` — call your llama.cpp/OpenAI and return the answer.
- For RAG over Finance Bill/GST PDFs: add a `vectorstore/` module and index + query routes.

## DB
SQLite for dev. Switch to Postgres by setting `DATABASE_URL=postgresql+psycopg://...` and re-running migrations.
=======
# AI-CA: AI-Powered Virtual Chartered Accountant

An intelligent tax computation and compliance dashboard that parses Indian income tax documents (Form 16, Form 26AS, AIS), extracts key data semantically, and computes accurate tax liability under both old and new regimes.

## 🌟 Features

1. **Document Verification**: Automatically verify Form 16, Form 26AS, and AIS with PAN and name matching
2. **AI-Based Tax Calculation**: Accurate computation under both old and new tax regimes
3. **Smart Regime Recommendation**: AI suggests the best regime with detailed explanations
4. **ITR Form Guidance**: Automatic recommendation of appropriate ITR form
5. **Graphical Dashboard**: Beautiful charts and visualizations for easy understanding
6. **Investment Suggestions**: Personalized recommendations to reduce taxable amount
7. **Q&A Assistant**: AI-powered chatbot for tax-related queries
8. **PDF Reports**: Downloadable comprehensive tax reports
9. **Year-wise Data Management**: Separate storage for each financial year
10. **Dynamic Tax Rules**: Easy-to-update year-wise tax regulations

## 🛠 Tech Stack

### Backend
- **Python FastAPI**: High-performance REST API
- **SQLAlchemy**: ORM for database management
- **SQLite**: Database (easily switchable to PostgreSQL/MySQL)
- **PyPDF2**: PDF parsing and text extraction
- **Ollama (Mistral 7B)**: AI model for data extraction and Q&A
- **JWT**: Secure authentication

### Frontend
- **React 18**: Modern UI library
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Beautiful data visualizations
- **React Router**: Client-side routing
- **Axios**: HTTP client
- **jsPDF**: PDF generation

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+**
- **Node.js 18+** and npm
- **Ollama** with Mistral 7B model

### Installing Ollama

1. Download and install Ollama from [https://ollama.ai](https://ollama.ai)
2. Pull the Mistral model:
   ```bash
   ollama pull mistral:7b-instruct
   ```
3. Verify installation:
   ```bash
   ollama list
   ```

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
cd "C:\Users\DELL\OneDrive\Desktop\New AICA"
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed tax rules into database
python seed_tax_rules.py

# Run the backend server
python main.py
```
uvicorn main:app --reload

The backend will start at `http://localhost:8000`

### 3. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start at `http://localhost:3000`

### 4. Verify Ollama is Running

```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve
```

## 📖 Usage Guide

### First Time Setup

1. **Register**: Create an account with your PAN card details
2. **Login**: Access your dashboard using PAN or email
3. **Upload Documents**: Upload Form 16, Form 26AS, and AIS (PDF only)
4. **Wait for Verification**: Documents are automatically verified
5. **Calculate Tax**: Click "Calculate Tax" after verification
6. **Review Results**: Check both regimes and AI recommendation
7. **Get Suggestions**: Generate investment suggestions
8. **Download Report**: Export comprehensive PDF report

### Document Requirements

- **Format**: PDF only
- **Name Match**: Your name must match the document
- **PAN Match**: Your PAN must match the document
- **Types Supported**:
  - Form 16 (TDS Certificate for Salary)
  - Form 26AS (Tax Credit Statement)
  - AIS (Annual Information Statement)

### Tax Calculation

The system calculates:
- Gross Total Income
- Deductions (Old Regime: 80C, 80D, etc.)
- Taxable Income (both regimes)
- Tax before rebate
- Rebate under Section 87A
- Surcharge and Cess
- Final Tax Liability
- TDS adjustment
- Tax Payable/Refund

### Investment Suggestions

Based on your profile, AI suggests:
- Tax-saving investments (80C, 80D, etc.)
- Recommended amounts
- Potential tax savings
- Risk levels
- Detailed explanations

## 🗂 Project Structure

```
New AICA/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── auth.py                 # Authentication utilities
│   ├── dependencies.py         # FastAPI dependencies
│   ├── seed_tax_rules.py       # Database seeder
│   ├── requirements.txt        # Python dependencies
│   ├── routers/
│   │   ├── auth.py            # Authentication routes
│   │   ├── documents.py       # Document management routes
│   │   ├── tax.py             # Tax calculation routes
│   │   ├── dashboard.py       # Dashboard routes
│   │   ├── qna.py             # Q&A routes
│   │   └── investments.py     # Investment suggestion routes
│   └── utils/
│       ├── pdf_processor.py   # PDF parsing and verification
│       ├── ollama_client.py   # Ollama API client
│       └── tax_calculator.py  # Tax calculation engine
├── frontend/
│   ├── src/
│   │   ├── main.jsx           # React entry point
│   │   ├── App.jsx            # Main App component
│   │   ├── index.css          # Global styles
│   │   ├── context/
│   │   │   └── AuthContext.jsx # Authentication context
│   │   ├── services/
│   │   │   └── api.js         # API client
│   │   ├── components/
│   │   │   └── Layout.jsx     # Dashboard layout
│   │   └── pages/
│   │       ├── LandingPage.jsx
│   │       ├── Login.jsx
│   │       ├── Register.jsx
│   │       ├── Dashboard.jsx
│   │       ├── Documents.jsx
│   │       ├── TaxCalculation.jsx
│   │       ├── Investments.jsx
│   │       ├── QnA.jsx
│   │       └── Benefits.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
└── README.md
```

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file in the backend directory (optional):

```env
DATABASE_URL=sqlite:///./aica.db
SECRET_KEY=your-secret-key-change-in-production
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b-instruct
```

### Adding New Financial Year Rules

1. Update `backend/seed_tax_rules.py` with new year's rules
2. Run the seeder:
   ```bash
   python seed_tax_rules.py
   ```

## 📊 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎨 UI Screenshots

The application features:
- Modern, responsive design
- Intuitive navigation
- Beautiful data visualizations
- Mobile-friendly interface
- Accessible color schemes

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Secure file upload validation
- Year-wise data isolation
- PAN and name verification

## 📝 Key Highlights

### Dynamic Tax Rules
- Tax rules stored in database as JSON
- Easy to update for new financial years
- Supports complex slab structures
- Handles age-based exemptions

### AI-Powered Intelligence
- Document verification using Ollama
- Smart data extraction from unstructured PDFs
- Natural language Q&A
- Personalized investment suggestions
- Regime recommendation with reasoning

### Comprehensive Features
- Complete tax calculation workflow
- Visual dashboards with charts
- Activity tracking and history
- PDF report generation
- Investment planning

## 🐛 Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama if needed
ollama serve
```

### Database Issues
```bash
# Delete and recreate database
cd backend
rm aica.db
python seed_tax_rules.py
```

### Frontend Build Issues
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 🚀 Deployment

### Backend Deployment (Production)

1. Use PostgreSQL instead of SQLite
2. Set strong SECRET_KEY
3. Enable CORS for production domain
4. Use gunicorn or uvicorn workers
5. Set up proper logging

### Frontend Deployment

```bash
cd frontend
npm run build
# Deploy 'dist' folder to hosting service
```

## 📄 License

This project is created for tax compliance purposes. Ensure compliance with local regulations when deploying.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns
- Tax calculations are accurate
- UI remains responsive
- Documentation is updated

## ⚠️ Disclaimer

This application provides tax calculations based on Indian Income Tax rules. Always consult with a qualified Chartered Accountant before filing your taxes. The AI suggestions are for informational purposes only.

## 📞 Support

For issues and questions:
- Check the documentation
- Review API docs at /docs
- Verify Ollama is running
- Check console for errors

## 🎯 Future Enhancements

- Multi-user tenant support
- E-filing integration
- Advanced tax planning scenarios
- More investment categories
- Mobile application
- Automated ITR form filling
- Integration with income tax portal

---
