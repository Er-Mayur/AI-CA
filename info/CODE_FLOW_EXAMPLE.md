# 💻 CODE FLOW: Line-by-Line Example

## 🎯 Real Example: Processing "Gopal Mahajan Form 16.pdf"

Let's trace **exactly** what happens when you upload a Form 16.

---

## 📤 **User Action**

```javascript
// Frontend: User uploads file
const formData = new FormData();
formData.append('file', pdfFile);
formData.append('financial_year', '2024-25');
formData.append('doc_type', 'Form 16');

await api.post('/documents/upload', formData);
```

---

## 📥 **Backend Receives Upload**

### **File:** `backend/routers/documents.py`

```python
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    financial_year: str = Form(...),  # "2024-25"
    doc_type: str = Form(...),         # "Form 16"
    current_user: User = Depends(get_current_user),  # PAN: AGDPM8485G
    db: Session = Depends(get_db)
):
    # Save file
    file_path = "uploads/1/2024-25/Form 16_1762359986.435609.pdf"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Verify document
    verification_result = await verify_document(
        file_path,
        current_user.name,        # "Gopal Madhavrao Mahajan"
        current_user.pan_card,    # "AGDPM8485G"
        DocType.FORM_16,
        financial_year            # "2024-25"
    )
```

---

## 🔬 **STAGE 1: Extract Text from PDF**

### **File:** `backend/utils/pdf_processor.py`

```python
async def verify_document(file_path, user_name, user_pan, doc_type, expected_fy):
    print(f"🔍 VERIFICATION STARTED")
    print(f"Expected PAN: {user_pan}")        # AGDPM8485G
    print(f"Expected FY: {expected_fy}")      # 2024-25
    
    # STEP 1: Extract text
    text = extract_text_from_pdf_advanced(file_path)
    # ↓
```

### **File:** `backend/utils/pdf_processor.py`

```python
def extract_text_from_pdf_advanced(file_path):
    extraction_results = {}
    
    # Try Method 1: pdfplumber
    with pdfplumber.open(file_path) as pdf:
        print(f"📄 PDF has {len(pdf.pages)} pages")  # 2 pages
        
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            text += page_text + "\n"
        
        extraction_results['pdfplumber'] = text
        print(f"📝 pdfplumber: {len(text)} chars")  # 2,345 chars
    
    # Try Method 2: pdfminer
    text = pdfminer_extract_text(file_path)
    extraction_results['pdfminer'] = text
    print(f"📝 pdfminer: {len(text)} chars")  # 2,198 chars
    
    # Try Method 3: PyPDF2
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        extraction_results['PyPDF2'] = text
        print(f"📝 PyPDF2: {len(text)} chars")  # 1,987 chars
    
    # Select best extraction
    best_method = max(extraction_results.items(), key=lambda x: len(x[1]))
    print(f"✅ Using {best_method[0]}: {len(best_method[1])} chars")
    
    return best_method[1]  # pdfplumber text (2,345 chars)
```

### **Extracted Text (first 500 chars):**

```
FORM NO. 16
[CERTIFICATE UNDER SECTION 203 OF THE INCOME-TAX ACT, 1961 FOR TAX DEDUCTED AT SOURCE ON SALARY]

PART A
(See section 203 and rule 31(1)(a) of the Income-tax Rules, 1962)

Name and address of the Employer:
HITACHI ASTEMO LTD
BANGALORE - 560100
TAN: BANG12345E

Name and designation of the Employee:
GOPAL MADHAVRAO MAHAJAN
PAN: AGDPM8485G

Financial Year: 2024-25
Assessment Year: 2025-26

Period: From 01-04-2024 To 31-03-2025
...
```

---

## 🔬 **STAGE 2: Smart Pattern Extraction**

```python
# Back in verify_document():
print(f"🔍 Running SMART pattern extraction...")

extracted = extract_with_smart_extractor(
    text,
    user_name="Gopal Madhavrao Mahajan",
    user_pan="AGDPM8485G"
)
# ↓
```

### **File:** `backend/utils/smart_extractor.py`

```python
def extract_with_smart_extractor(text, user_name, user_pan):
    extractor = SmartExtractor(text, user_name, user_pan)
    return extractor.extract_all_data()

class SmartExtractor:
    def __init__(self, text, user_name, user_pan):
        self.original_text = text
        self.text = normalize_spaces(text.upper())  # Clean text
        self.user_name = user_name
        self.user_pan = user_pan
    
    def extract_all_data(self):
        result = {}
        
        # Extract PAN
        print("   Looking for PAN...")
        result['pan'] = self._extract_pan_smart()
        # ↓
```

### **PAN Extraction:**

```python
def _extract_pan_smart(self):
    # User's known PAN
    if self.user_pan:
        user_pan_clean = "AGDPM8485G"
        if user_pan_clean in self.text:
            print(f"   ✅ Found user's PAN: {user_pan_clean}")
            return user_pan_clean
    
    # Extract all PANs from text
    all_pans = extract_all_pans(self.text)
    # Regex: [A-Z]{5}\d{4}[A-Z]
    # Found: ['AGDPM8485G', 'AAACH1234A']
    
    print(f"   All PANs found: {all_pans}")
    
    # Distinguish employee vs employer
    for pan in all_pans:
        context = self._get_text_around(pan, 100)
        # For AGDPM8485G:
        # "...EMPLOYEE NAME: GOPAL MAHAJAN PAN: AGDPM8485G..."
        
        if 'EMPLOYEE' in context and 'EMPLOYER' not in context:
            print(f"   ✅ Selected employee PAN: {pan}")
            return pan
    
    return all_pans[0]

# Result: "AGDPM8485G"
```

### **Financial Year Extraction:**

```python
# Back in extract_all_data():
print("   Looking for Financial Year...")
result['financial_year'] = pick_fy(self.text)
# ↓

def pick_fy(text):
    # Pattern 1: "Financial Year: 2024-25"
    pattern = r'Financial\s+Year\s*[:\-]?\s*(\d{4})\s*-\s*(\d{2,4})'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        year1 = match.group(1)  # "2024"
        year2 = match.group(2)  # "25"
        
        # Normalize
        if len(year2) == 4:
            year2 = year2[-2:]
        
        fy = f"{year1}-{year2}"
        print(f"   ✅ Found FY: {fy}")
        return fy  # "2024-25"
    
    return None

# Result: "2024-25"
```

### **Document Type Detection:**

```python
# Back in extract_all_data():
print("   Looking for Document Type...")
result['document_type'] = extract_document_type(self.text)
# ↓

def extract_document_type(text):
    text_upper = text.upper()
    
    # Check for Form 16 keywords
    form16_keywords = [
        'FORM 16', 'FORM NO. 16', 
        'CERTIFICATE UNDER SECTION 203'
    ]
    
    for keyword in form16_keywords:
        if keyword in text_upper:
            print(f"   ✅ Found keyword: '{keyword}'")
            print(f"   ✅ Document Type: Form 16")
            return "Form 16"
    
    return None

# Result: "Form 16"
```

### **Name Extraction:**

```python
# Back in extract_all_data():
print("   Looking for Name...")
result['name'], result['all_names_found'] = self._extract_name_smart()
# ↓

def _extract_name_smart(self):
    all_names = []
    
    # Look for name near PAN
    pan = "AGDPM8485G"
    name_from_pan = self._extract_name_near_pan(pan)
    # ↓
    
def _extract_name_near_pan(self, pan):
    # Find PAN in text
    pan_index = self.text.find("AGDPM8485G")  # index: 450
    
    # Get context (500 chars before and after)
    context = self.text[max(0, 450-500):min(len(self.text), 450+500)]
    
    # Context:
    # "...EMPLOYEE NAME: GOPAL MADHAVRAO MAHAJAN PAN: AGDPM8485G..."
    
    # Pattern: "NAME: [CAPS TEXT]"
    pattern = r'NAME\s*[:\-]?\s*([A-Z][A-Z\s\.]{2,50})'
    match = re.search(pattern, context)
    
    if match:
        name = match.group(1).strip()  # "GOPAL MADHAVRAO MAHAJAN"
        
        # Validate
        if self._is_valid_name(name):
            print(f"   ✅ Found name: {name}")
            return self._format_name(name)  # "Gopal Madhavrao Mahajan"
    
    return None

# Result: "Gopal Madhavrao Mahajan"
```

### **Complete Extraction Result:**

```python
# Back in extract_all_data():
print("📊 Smart Extraction Results:")

extracted = {
    'pan': 'AGDPM8485G',
    'name': 'Gopal Madhavrao Mahajan',
    'financial_year': '2024-25',
    'document_type': 'Form 16',
    'employer_name': 'Hitachi Astemo Ltd',
    'employer_tan': 'BANG12345E',
    'all_pans_found': ['AGDPM8485G', 'AAACH1234A'],
    'all_names_found': ['Gopal Madhavrao Mahajan'],
    'extraction_confidence': 1.0  # 100%
}

print(f"   PAN: {extracted['pan']}")
print(f"   Name: {extracted['name']}")
print(f"   FY: {extracted['financial_year']}")
print(f"   Doc Type: {extracted['document_type']}")
print(f"   Confidence: {extracted['extraction_confidence']:.0%}")

return extracted
```

---

## 🔬 **STAGE 3: AI Fallback (Skipped)**

```python
# Back in verify_document():

# Check confidence
if extracted['extraction_confidence'] < 0.7:
    print("⚠️  Low confidence, using AI...")
    ai_data = await extract_data_with_ai(text, doc_type, expected_fy)
else:
    print("✅ High confidence (100%), skipping AI")
    # Confidence = 100%, so we skip AI
```

---

## 🔬 **STAGE 4: Verification**

```python
# Back in verify_document():
print("🔐 Verifying critical fields...")

# VERIFY PAN
extracted_pan = extracted['pan']         # "AGDPM8485G"
expected_pan = user_pan                  # "AGDPM8485G"

if extracted_pan.upper() != expected_pan.upper():
    return {
        "verified": False,
        "message": f"PAN mismatch! Expected {expected_pan}, found {extracted_pan}"
    }

print(f"✅ PAN VERIFIED: {extracted_pan}")

# VERIFY FINANCIAL YEAR
extracted_fy = extracted['financial_year']  # "2024-25"
expected_fy_param = expected_fy             # "2024-25"

if extracted_fy != expected_fy_param:
    return {
        "verified": False,
        "message": f"FY mismatch! Expected {expected_fy_param}, found {extracted_fy}"
    }

print(f"✅ FINANCIAL YEAR VERIFIED: {extracted_fy}")

# Log other info
print(f"ℹ️  Name found: {extracted['name']}")
print(f"ℹ️  Doc Type: {extracted['document_type']}")
print(f"ℹ️  Employer: {extracted['employer_name']}")

# SUCCESS!
print("\n" + "="*60)
print("✅ VERIFICATION SUCCESSFUL!")
print("="*60)
print(f"✅ PAN: {extracted_pan} ← Matches your PAN")
print(f"✅ Financial Year: {extracted_fy} ← Matches selected FY")
print("="*60)

return {
    "verified": True,
    "message": f"✅ Document verified! PAN: {extracted_pan}, FY: {extracted_fy}",
    "extracted_data": extracted
}
```

---

## 📝 **STAGE 5: Save to Database**

```python
# Back in routers/documents.py:

verification_result = await verify_document(...)

if verification_result["verified"]:
    # Update document status
    document.verification_status = VerificationStatus.VERIFIED
    document.verification_message = verification_result["message"]
    document.verified_at = datetime.utcnow()
    document.extracted_data = verification_result["extracted_data"]
    
    db.commit()
    
    # Log activity
    activity = ActivityHistory(
        user_id=current_user.id,
        financial_year=financial_year,
        activity_type="DOCUMENT_VERIFIED",
        description=f"Form 16 verified for FY 2024-25"
    )
    db.add(activity)
    db.commit()
```

---

## 📤 **Response to Frontend**

```json
{
  "id": 7,
  "user_id": 1,
  "financial_year": "2024-25",
  "doc_type": "Form 16",
  "file_path": "uploads/1/2024-25/Form 16_1762359986.435609.pdf",
  "verification_status": "verified",
  "verification_message": "✅ Document verified! PAN: AGDPM8485G, FY: 2024-25",
  "extracted_data": {
    "pan": "AGDPM8485G",
    "name": "Gopal Madhavrao Mahajan",
    "financial_year": "2024-25",
    "document_type": "Form 16",
    "employer_name": "Hitachi Astemo Ltd",
    "employer_tan": "BANG12345E",
    "extraction_confidence": 1.0
  },
  "uploaded_at": "2025-11-05T16:39:50.572768",
  "verified_at": "2025-11-05T16:39:52.123456"
}
```

---

## 🎯 **Console Output (Complete)**

```
============================================================
🔍 SIMPLIFIED VERIFICATION STARTED
============================================================
✅ Expected PAN: AGDPM8485G
✅ Expected FY: 2024-25
📄 Document Type: Form 16
============================================================

📄 PDF has 2 page(s)
📝 pdfplumber: 2345 chars from 2 pages
📝 pdfminer: 2198 chars
📝 PyPDF2: 1987 chars
✅ Using pdfplumber: 2345 chars (best result)

✅ Text extracted: 2345 characters
📄 Preview (first 300 chars):
FORM NO. 16
[CERTIFICATE UNDER SECTION 203 OF THE INCOME-TAX ACT, 1961
FOR TAX DEDUCTED AT SOURCE ON SALARY]
PART A
Name and address of the Employer:
HITACHI ASTEMO LTD
BANGALORE - 560100
TAN: BANG12345E
Name and designation of the Employee:
GOPAL MADHAVRAO MAHAJAN
PAN: AGDPM8485G
Financial Year: 2024-25
...

🔍 Running SMART pattern extraction...
   Looking for PAN...
   ✅ Found user's PAN: AGDPM8485G
   All PANs found: ['AGDPM8485G', 'AAACH1234A']
   
   Looking for Financial Year...
   ✅ Found FY: 2024-25
   
   Looking for Document Type...
   ✅ Found keyword: 'FORM NO. 16'
   ✅ Document Type: Form 16
   
   Looking for Name...
   ✅ Found name: GOPAL MADHAVRAO MAHAJAN

📊 Smart Extraction Results:
   PAN: AGDPM8485G
   Name: Gopal Madhavrao Mahajan
   FY: 2024-25
   Doc Type: Form 16
   Employer: Hitachi Astemo Ltd
   TAN: BANG12345E
   All PANs Found: AGDPM8485G, AAACH1234A
   All Names Found: Gopal Madhavrao Mahajan
   Confidence: 100%

✅ High confidence (100%), skipping AI

🔐 Verifying critical fields (PAN + Financial Year)...
✅ PAN VERIFIED: AGDPM8485G
✅ FINANCIAL YEAR VERIFIED: 2024-25

ℹ️  Name found in document: Gopal Madhavrao Mahajan
ℹ️  Document type detected: Form 16
ℹ️  Employer: Hitachi Astemo Ltd

============================================================
✅ VERIFICATION SUCCESSFUL!
============================================================
✅ PAN: AGDPM8485G ← Matches your PAN
✅ Financial Year: 2024-25 ← Matches selected FY
============================================================
```

---

## 🎉 **Summary: Data Flow**

```
PDF File (Binary)
    ↓ pdfplumber.extract_text()
Raw Text (2,345 chars)
    ↓ normalize_spaces()
Clean Text (uppercase, normalized)
    ↓ regex: [A-Z]{5}\d{4}[A-Z]
PAN: "AGDPM8485G"
    ↓ regex: Financial\s+Year.*(\d{4})-(\d{2})
FY: "2024-25"
    ↓ keyword: "FORM NO. 16"
Doc Type: "Form 16"
    ↓ pattern: NAME.*([A-Z\s\.]+)
Name: "Gopal Madhavrao Mahajan"
    ↓ comparison
Verify: PAN == user.pan && FY == selected_fy
    ↓
✅ VERIFIED!
```

---

## 💡 **Key Takeaway**

Every field is extracted using:
1. **Regex patterns** (deterministic, fast)
2. **Context awareness** (employee vs employer)
3. **AI fallback** (when regex fails)
4. **Validation** (against user profile)

**100% offline. Zero cloud dependencies.** 🎯

