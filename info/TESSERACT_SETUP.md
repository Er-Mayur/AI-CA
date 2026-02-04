# 🔍 OCR Setup Guide (Tesseract + Poppler)

For **100% accurate document verification** including scanned PDFs, you need to install **both** Tesseract and Poppler.

## 📦 Windows Installation

### Step 1: Install Poppler (Required for PDF to Image Conversion)

**Method 1: Direct Download (Recommended)**

1. **Download Poppler:**
   - Go to: https://github.com/oschwartz10612/poppler-windows/releases
   - Download latest `Release-XX.XX.X-X.zip`

2. **Extract:**
   - Extract ZIP to `C:\Program Files\poppler` (or any location)
   - You should have folders like: `bin`, `include`, `lib`, `share`

3. **Add to PATH:**
   - Open System Properties → Environment Variables
   - Edit `PATH` variable
   - Add: `C:\Program Files\poppler\Library\bin` (or wherever you extracted + `\Library\bin`)
   - Click OK

4. **Verify:**
   ```cmd
   pdftoppm -h
   ```
   Should show help text (not "command not found")

**Method 2: Using Chocolatey**

```cmd
choco install poppler
```

---

### Step 2: Install Tesseract (OCR Engine)

**Method 1: Direct Download (Recommended)**

1. **Download Tesseract Installer:**
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download: `tesseract-ocr-w64-setup-5.3.3.20231005.exe` (or latest version)

2. **Install:**
   - Run the installer
   - **IMPORTANT:** During installation, note the installation path (usually `C:\Program Files\Tesseract-OCR`)
   - Keep all default settings
   - Click "Install"

3. **Add to PATH (if needed):**
   - Open System Properties → Environment Variables
   - Edit `PATH` variable
   - Add: `C:\Program Files\Tesseract-OCR`
   - Restart terminal

4. **Verify Installation:**
   ```cmd
   tesseract --version
   ```
   Should show version info

**Method 2: Using Chocolatey**

```cmd
choco install tesseract
```

---

## 🐧 Linux Installation

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### CentOS/RHEL:
```bash
sudo yum install tesseract
```

---

## 🍎 macOS Installation

```bash
brew install tesseract
```

---

---

## ✅ Verify Installation

### Test Poppler:
```cmd
pdftoppm -h
```
Should show help text (not error)

### Test Tesseract:
```cmd
tesseract --version
```
Should show version like `tesseract 5.3.3`

### Test Python Integration:
```bash
cd backend
.\venv\Scripts\Activate.ps1  # Windows

python -c "import pytesseract; from pdf2image import convert_from_path; print('✅ OCR is ready!')"
```

If this works, you're all set!

---

## 🚀 What This Enables

Once Tesseract is installed:

✅ **Scanned PDF support** - Extract text from image-based PDFs  
✅ **Form 16 images** - Process scanned Form 16 documents  
✅ **Photo uploads** - Handle mobile-captured tax documents  
✅ **100% extraction** - Works with ANY PDF, even low-quality scans  

---

## 🔧 Troubleshooting

### Error: "tesseract is not installed"

**Solution:** Install Tesseract using one of the methods above.

### Error: "Unable to find tesseract executable"

**Solution:** 
1. Find where Tesseract is installed
2. Add it to your system PATH
3. Restart your terminal/IDE

### OCR is slow

**Normal behavior:** OCR processing takes 10-30 seconds for multi-page PDFs.
The system will automatically use faster methods (pdfplumber) for text-based PDFs.

---

## 📝 Notes

- The system works **WITHOUT Tesseract** for regular text-based PDFs
- Tesseract is **ONLY needed** for scanned/image PDFs
- All processing is **100% offline** - no cloud APIs used
- OCR runs locally using your CPU/GPU

---

## 🎯 Quick Test

Upload a Form 16 PDF and check the backend console:

```
📝 pdfplumber extraction: 5234 chars    ← Text-based PDF (fast)
🔍 Trying OCR extraction...              ← Scanned PDF (slower)
📝 OCR extraction: 4821 chars            ← OCR successful
```

