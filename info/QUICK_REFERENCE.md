# AI-CA Quick Reference Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Start Ollama
```bash
# Double-click start_ollama.bat
# OR run in terminal:
ollama serve
```

### Step 2: Start Backend
```bash
# Double-click start_backend.bat
# OR run manually:
cd backend
venv\Scripts\activate
python main.py
```

### Step 3: Start Frontend
```bash
# Double-click start_frontend.bat
# OR run manually:
cd frontend
npm run dev
```

**Open Browser**: http://localhost:3000

---

## 📋 Important URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main application |
| Backend API | http://localhost:8000 | REST API |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API docs |
| API Docs (ReDoc) | http://localhost:8000/redoc | Alternative docs |
| Ollama API | http://localhost:11434 | AI model server |

---

## 🎯 User Journey

1. **Landing Page** → Click "Get Started"
2. **Register** → Fill form with PAN details
3. **Dashboard** → View overview
4. **Documents** → Upload Form 16, 26AS, AIS
5. **Wait** → Documents auto-verify
6. **Tax Calculation** → Click "Calculate Tax"
7. **View Results** → See both regimes, get recommendation
8. **Investments** → Generate suggestions
9. **Download** → Get PDF reports

---

## 📄 Supported Documents

| Document | Description | Required |
|----------|-------------|----------|
| Form 16 | TDS Certificate from Employer | Yes |
| Form 26AS | Tax Credit Statement | Recommended |
| AIS | Annual Information Statement | Recommended |

**Requirements**:
- Must be PDF format
- Name must match registration
- PAN must match registration

---

## 💰 Tax Calculation Flow

```
Upload Documents
    ↓
Verify (Name + PAN)
    ↓
Extract Data (AI)
    ↓
Calculate Both Regimes
    ↓
Compare Results
    ↓
Get Recommendation
    ↓
Download Report
```

---

## 🔐 Authentication

### Registration Fields
- Full Name (as per PAN)
- PAN Card (10 characters)
- Email
- Gender
- Date of Birth
- Password (min 6 chars)

### Login Options
- PAN Number + Password
- Email + Password

---

## 📊 Dashboard Features

### Overview Cards
- Documents Uploaded/Verified
- Tax Computation Status
- Gross Income
- Tax Payable/Refund

### Charts
- Income & Tax Breakdown (Bar Chart)
- Tax Distribution (Pie Chart)

### Activity History
- Recent actions with timestamps

---

## 🧮 Tax Features

### Old Regime
- Age-based slabs
- Multiple deductions (80C, 80D, etc.)
- Standard deduction
- HRA exemption

### New Regime
- Lower tax rates
- Limited deductions
- Standard deduction
- Simpler structure

### Both Regimes Calculate
- Gross Total Income
- Total Deductions
- Taxable Income
- Tax Before Rebate
- Rebate u/s 87A
- Surcharge
- Health & Education Cess (4%)
- Final Tax Liability

---

## 💡 Investment Suggestions

AI analyzes your profile and suggests:
- Section 80C investments (₹1.5 lakh limit)
- Section 80D health insurance
- Section 80CCD(1B) NPS
- Section 24(b) home loan interest
- Other tax-saving options

Each suggestion includes:
- Investment type
- Recommended amount
- Potential tax savings
- Risk level
- Detailed explanation

---

## 💬 Q&A Assistant

### How to Use
1. Type your question
2. Get instant AI answer
3. View sources/references

### Sample Questions
- "What is Section 80C?"
- "Which regime is better for me?"
- "What is the deadline for ITR filing?"
- "Can I claim HRA exemption?"

### Quick Questions
- Pre-loaded common questions
- Click to ask instantly
- Categorized by topic

---

## 📥 Downloads

### Tax Computation PDF
- Income breakdown
- Both regime calculations
- Recommendation
- ITR form guidance
- Final tax liability

### Benefits Summary PDF
- Total savings
- Features used
- Regime comparison
- Investment suggestions

---

## 🎨 Color Scheme

- Primary: Blue (#0ea5e9)
- Success: Green
- Warning: Yellow
- Error: Red
- Gray: Neutral backgrounds

---

## ⌨️ Keyboard Shortcuts

- **Ctrl+/** - Focus search (if implemented)
- **F12** - Open browser console for debugging

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend Won't Start
```bash
cd frontend
npm install
npm run dev
```

### Ollama Not Responding
```bash
ollama serve
ollama list
ollama pull mistral:7b-instruct
```

### Database Issues
```bash
cd backend
del aica.db
python seed_tax_rules.py
```

---

## 📱 Browser Support

- ✅ Chrome (Recommended)
- ✅ Firefox
- ✅ Edge
- ✅ Safari

---

## 🔒 Security

- Passwords: Hashed with bcrypt
- Sessions: JWT tokens (7 days)
- Files: Validated and stored securely
- Data: User-isolated, year-wise

---

## 📞 API Endpoints

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/list/{year}` - List documents
- `DELETE /api/documents/{id}` - Delete document

### Tax
- `POST /api/tax/calculate/{year}` - Calculate tax
- `GET /api/tax/computation/{year}` - Get computation

### Dashboard
- `GET /api/dashboard/stats/{year}` - Get statistics
- `GET /api/dashboard/activities/{year}` - Get activities
- `GET /api/dashboard/current-year` - Get current FY

### Investments
- `POST /api/investments/suggest/{year}` - Generate suggestions
- `GET /api/investments/suggestions/{year}` - Get suggestions

### Q&A
- `POST /api/qna/ask` - Ask question
- `GET /api/qna/common-questions` - Get FAQ

---

## 💾 Database Tables

1. **users** - User accounts
2. **documents** - Uploaded files
3. **tax_computations** - Tax calculations
4. **tax_rules** - Year-wise rules
5. **activity_history** - User actions
6. **investment_suggestions** - AI suggestions

---

## 🎓 Tax Terminology

| Term | Meaning |
|------|---------|
| FY | Financial Year (Apr 1 - Mar 31) |
| AY | Assessment Year (next year) |
| PAN | Permanent Account Number |
| TDS | Tax Deducted at Source |
| ITR | Income Tax Return |
| HRA | House Rent Allowance |
| GTI | Gross Total Income |

---

## 📈 Supported Tax Sections

### Deductions (Old Regime)
- 80C (₹1.5L) - LIC, PPF, ELSS, etc.
- 80D (₹25K/50K) - Health insurance
- 80E - Education loan interest
- 80G - Donations
- 80TTA - Savings interest
- 24(b) - Home loan interest

### Rebate
- 87A - Up to ₹12,500 (Old) / ₹25,000 (New)

---

## 🎯 Pro Tips

1. **Upload All Documents** - For accurate calculation
2. **Verify Before Calculating** - Ensure documents are verified
3. **Compare Regimes** - Don't assume one is always better
4. **Save PDFs** - Download reports for records
5. **Ask Questions** - Use Q&A for clarifications
6. **Review Suggestions** - Consider investment recommendations
7. **Check Activity Log** - Monitor all actions
8. **Update Yearly** - New tax rules added annually

---

## 📅 Important Dates (General)

- **April 1** - Financial year starts
- **March 31** - Financial year ends
- **July 31** - ITR filing deadline (non-audit)
- **December 31** - Belated return deadline

---

## 🏁 Getting Help

1. Check browser console (F12)
2. Check backend terminal logs
3. Verify Ollama is running
4. Check API docs at /docs
5. Review SETUP_INSTRUCTIONS.md
6. Check README.md

---

## 🌟 Best Practices

### For Accuracy
- Upload clear, readable PDFs
- Ensure all required documents
- Verify extracted data
- Cross-check calculations

### For Security
- Use strong passwords
- Don't share credentials
- Logout after use
- Keep software updated

### For Performance
- Close unused tabs
- Clear browser cache if slow
- Restart services periodically
- Monitor disk space

---

**Last Updated**: FY 2024-25
**Version**: 1.0.0
**Status**: Production Ready ✅

