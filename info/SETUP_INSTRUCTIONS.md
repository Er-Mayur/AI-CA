# Quick Setup Instructions for AI-CA

## Step-by-Step Setup Guide

### Step 1: Install Prerequisites

#### 1.1 Install Python 3.9+
- Download from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Verify: `python --version`

#### 1.2 Install Node.js 18+
- Download from https://nodejs.org/
- Install LTS version
- Verify: `node --version` and `npm --version`

#### 1.3 Install Ollama
- Windows: Download from https://ollama.ai/download/windows
- Run the installer
- Open Command Prompt and run:
  ```bash
  ollama pull mistral:7b-instruct
  ```
- Verify: `ollama list`

### Step 2: Setup Backend

```bash
# Open Command Prompt or PowerShell
cd "C:\Users\DELL\OneDrive\Desktop\New AICA\backend"

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database with tax rules
python seed_tax_rules.py

# You should see: "✓ Tax rules seeded successfully!"
```

### Step 3: Setup Frontend

Open a NEW Command Prompt/PowerShell window:

```bash
cd "C:\Users\DELL\OneDrive\Desktop\New AICA\frontend"

# Install dependencies
npm install

# This will take a few minutes
```

### Step 4: Start Ollama (if not running)

Open a NEW Command Prompt window:

```bash
ollama serve
```

Keep this window open.

### Step 5: Start Backend Server

In the backend terminal (with venv activated):

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Keep this window open.

### Step 6: Start Frontend Server

In the frontend terminal:

```bash
npm run dev
```

You should see:
```
VITE ready in XXX ms
Local: http://localhost:3000/
```

### Step 7: Access the Application

Open your browser and go to:
```
http://localhost:3000
```

## Testing the Application

### 1. Register a New User
- Click "Get Started" or "Register"
- Fill in the form:
  - Name: Your Full Name
  - PAN: ABCDE1234F (10 characters)
  - Email: your@email.com
  - Gender: Select
  - Date of Birth: Choose
  - Password: Create a strong password
  - Confirm Password: Same as above
- Click "Create Account"

### 2. Upload Sample Documents
- Go to "Documents" page
- Select document type (Form 16 / Form 26AS / AIS)
- Upload a PDF file
- Wait for verification (automatically happens)

### 3. Calculate Tax
- Go to "Tax Calculation" page
- Click "Calculate Tax"
- View results with regime comparison

### 4. Get Investment Suggestions
- Go to "Investments" page
- Click "Generate Suggestions"
- View AI-powered recommendations

### 5. Ask Questions
- Go to "Q&A" page
- Type a tax-related question
- Get instant AI answers

### 6. View Benefits Summary
- Go to "Benefits" page
- See your total savings
- Download PDF summary

## Common Issues and Solutions

### Issue 1: Backend won't start
**Solution:**
```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
venv\Scripts\activate

# Check if all packages are installed
pip list

# If missing packages:
pip install -r requirements.txt
```

### Issue 2: Frontend won't start
**Solution:**
```bash
# Delete node_modules and reinstall
cd frontend
rmdir /s node_modules
del package-lock.json
npm install
```

### Issue 3: Ollama connection error
**Solution:**
1. Make sure Ollama is running: `ollama serve`
2. Check model is installed: `ollama list`
3. If model missing: `ollama pull mistral:7b-instruct`

### Issue 4: Database error
**Solution:**
```bash
cd backend
# Delete database and recreate
del aica.db
python seed_tax_rules.py
```

### Issue 5: Port already in use
**Solution:**
```bash
# Backend (if port 8000 is busy)
# In main.py, change port number

# Frontend (if port 3000 is busy)
# In vite.config.js, change port number
```

## Stopping the Application

1. Frontend: Press `Ctrl+C` in the frontend terminal
2. Backend: Press `Ctrl+C` in the backend terminal
3. Ollama: Press `Ctrl+C` in the Ollama terminal (or leave it running)

## Restarting the Application

Next time, you only need to:

1. Start Ollama (if not running):
   ```bash
   ollama serve
   ```

2. Start Backend:
   ```bash
   cd backend
   venv\Scripts\activate
   python main.py
   ```

3. Start Frontend:
   ```bash
   cd frontend
   npm run dev
   ```

## Directory Structure

Make sure you have:
```
New AICA/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── seed_tax_rules.py
│   └── ... (other files)
└── frontend/
    ├── package.json
    ├── src/
    └── ... (other files)
```

## Need Help?

1. Check backend logs in the terminal
2. Check frontend console in browser (F12)
3. Check browser Network tab for API errors
4. Verify all services are running:
   - Ollama: http://localhost:11434
   - Backend: http://localhost:8000/docs
   - Frontend: http://localhost:3000

## API Documentation

Once backend is running, visit:
- http://localhost:8000/docs - Interactive API documentation

## Next Steps

After successful setup:
1. Explore the landing page
2. Register a test user
3. Upload sample tax documents
4. Calculate taxes
5. Get investment suggestions
6. Try the Q&A feature
7. Download reports

---

**Congratulations! Your AI-CA system is now running! 🎉**

