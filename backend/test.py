from services.semantic_extractor import extract_metadata_from_text

sample_ocr_text = """
Annual Information Statement (AIS)

Part A - General Information

Permanent Account Number (PAN)

AGDPM8485G


01/06/1975

Address

Financial Year
Assessment Year

2024-25
2025-26

Aadhaar Number

XXXX XXXX 5906

Mobile Number

9420791180

Name of Assessee

GOPAL MADHAVRAO MAHAJAN

E-mail Address

303gmtax@gmail.com

PLOT - 33 VYANKATESH COLONY,SANE GURUJI COLONY JILHA PETH JALGAON,JALGAON H.O,JALGAON,JALGAON,425001,MAHARASHTRA

------------------------------------------------------------------------------------- Annual Information Statement (Part B) --------------------------------------------------------------------------------------

Part B1-Information relating to tax deducted or collected at source

(All amount values are in INR)

Salary

SR. NO.

INFORMATION CODE

1

TDS-192

SR. NO.

QUARTER

1

2

3

4

5

6

7

8

9

10

11

12

Q4(Jan-Mar)

Q4(Jan-Mar)

Q4(Jan-Mar)

Q3(Oct-Dec)

Q3(Oct-Dec)

Q3(Oct-Dec)

Q2(Jul-Sep)

Q2(Jul-Sep)

Q2(Jul-Sep)

Q1(Apr-Jun)

Q1(Apr-Jun)

Q1(Apr-Jun)

INFORMATION DESCRIPTION

Salary received (Section 192)

INFORMATION SOURCE

HITACHI ASTEMO INDIA PRIVATE LIMITED (PNEF01495E)

COUNT

12

AMOUNT

10,69,432


AMOUNT PAID/CREDITED

TDS DEDUCTED

TDS DEPOSITED STATUS

31/03/2025

28/02/2025

31/01/2025

31/12/2024

30/11/2024

31/10/2024

30/09/2024

31/08/2024

31/07/2024

30/06/2024

31/05/2024

30/04/2024

86,251

81,251

1,03,702

81,251

96,001

95,651

81,251

82,751

81,251

1,01,192

73,080

1,05,800

13,924

13,900

8,200

8,200

8,200

8,200

8,200

4,000

4,000

4,000

4,000

4,000

13,924 Active

13,900 Active

8,200 Active

8,200 Active

8,200 Active

8,200 Active

8,200 Active

4,000 Active

4,000 Active

4,000 Active

4,000 Active

4,000 Active

Note - If there is variation between the TDS/TCS information as displayed in Form26AS on TRACES portal, and the TDS/TCS information as displayed in AIS on Compliance Portal, the taxpayer may rely on the
information displayed on TRACES portal for the purpose of filing of tax return and for other tax compliance purposes.

Part B2-Information relating to specified financial transaction (SFT)

Dividend

SR. NO.

INFORMATION CODE

1

SFT-015

SR. NO. REPORTED ON DIVIDEND AMOUNT STATUS

1

14/05/2025

1 Active

INFORMATION DESCRIPTION

Dividend income (SFT-015)

INFORMATION SOURCE

BANK OF MAHARASHTRA (AACCB0774B.AB220)

SR. NO.

INFORMATION CODE

2

SFT-015

INFORMATION DESCRIPTION

Dividend income (SFT-015)

INFORMATION SOURCE

ZEE ENTERTAINMENT ENTERPRISES LIMITED (AAACZ0243R.AZ520)

SR. NO. REPORTED ON DIVIDEND AMOUNT STATUS

1

26/05/2025

1 Active

Interest from savings bank

SR. NO.

INFORMATION CODE

INFORMATION DESCRIPTION

INFORMATION SOURCE

3

SFT-016(SB)

SR. NO.

REPORTED ON

1

06/05/2025

Interest income (SFT-016) – Savings

HDFC BANK LIMITED (AAACH2702H.AB772)

ACCOUNT NUMBER

01801050019285

ACCOUNT TYPE

Saving

SR. NO.

INFORMATION CODE

INFORMATION DESCRIPTION

INFORMATION SOURCE

4

SFT-016(SB)

SR. NO.

REPORTED ON

1

22/05/2025

Interest income (SFT-016) – Savings

JALGAON JANATA SAHAKARI BANK LTD (AAAAJ0477D.AC616)

ACCOUNT NUMBER

003 0023 00018615

ACCOUNT TYPE

Saving

SR. NO.

INFORMATION CODE

INFORMATION DESCRIPTION

INFORMATION SOURCE

5

SFT-016(SB)

SR. NO.

REPORTED ON

1

23/05/2025

SR. NO.

INFORMATION CODE

6

SFT-016(SB)

SR. NO.

REPORTED ON

1

30/05/2025

Interest from deposit

Interest income (SFT-016) – Savings

STATE BANK OF INDIA (AAACS8577K.AB703)

ACCOUNT NUMBER

00000030755570229

ACCOUNT TYPE

Saving

INFORMATION DESCRIPTION

INFORMATION SOURCE

Interest income (SFT-016) – Savings

THE JALGAON DISTRICT CENTRAL CO OP BANK LIMITED
(AAAAJ0225F.AC226)

ACCOUNT NUMBER

8120792021003164

ACCOUNT TYPE

Saving

SR. NO.

INFORMATION CODE

INFORMATION DESCRIPTION

INFORMATION SOURCE

Interest income (SFT-016) – Term Deposit

HDFC BANK LIMITED (AAACH2702H.AB772)

COUNT

1

COUNT

1

COUNT

1

INTEREST AMOUNT STATUS

1,257 Active

COUNT

1

INTEREST AMOUNT STATUS

117 Active

COUNT

1

INTEREST AMOUNT STATUS

87 Active

COUNT

1

INTEREST AMOUNT STATUS

38 Active

AMOUNT

1

AMOUNT

1

AMOUNT

1,257

AMOUNT

117

AMOUNT

87

AMOUNT

38

COUNT

7

AMOUNT

5,444

7

SFT-016(TD)

SR. NO.

REPORTED ON

1

2

3

4

5

6

06/05/2025

06/05/2025

06/05/2025

06/05/2025

06/05/2025

06/05/2025

Download ID : AGDPM8485G202510101820


ACCOUNT NUMBER

ACCOUNT TYPE

INTEREST AMOUNT STATUS

50301030866101

50301021695330

50301057877573

50301091417322

50301030863591

50301021698464

Time Deposit

Time Deposit

Time Deposit

Time Deposit

Time Deposit

Time Deposit

IP Address : 152.56.15.211

443 Active

221 Active

1,501 Active

621 Active

1,108 Active

1,107 Active

Page 1 of 2


PAN
AGDPM8485G

Name
GOPAL MADHAVRAO MAHAJAN

Assessment Year
2025-26

SR. NO.

REPORTED ON

7

06/05/2025

ACCOUNT NUMBER

50301046378240

ACCOUNT TYPE

Time Deposit

SR. NO.

INFORMATION CODE

INFORMATION DESCRIPTION

INFORMATION SOURCE

8

SFT-016(TD)

SR. NO.

REPORTED ON

1

22/05/2025

Purchase of securities and units of mutual funds

Interest income (SFT-016) – Term Deposit

JALGAON JANATA SAHAKARI BANK LTD (AAAAJ0477D.AC616)

ACCOUNT NUMBER

003 0037 00053595

ACCOUNT TYPE

Time Deposit

INTEREST AMOUNT STATUS

443 Active

COUNT

1

INTEREST AMOUNT STATUS

592 Active

AMOUNT

592

SR. NO.

INFORMATION CODE

INFORMATION DESCRIPTION

INFORMATION SOURCE

9

SFT-18(Pur)

Purchase of mutual funds (SFT - 018)

Computer Age Management Services Limited - HDFC Asset
Management Company Limited(H) (AAACC3035G.AZ670)

COUNT

2

AMOUNT

62,347

SR. NO.

QUARTER

1

2

Q4(Jan-Mar)

Q2(Jul-Sep)

CLIENT ID

24882499

24882499

AMC NAME (CODE)

HOLDER FLAG

TOTAL PURCHASE AMOUNT

TOTAL SALES VALUE STATUS

HDFC Asset Management
Company Limited(H)

HDFC Asset Management
Company Limited(H)

First

First

31,848

30,499

0 Active

0 Active

Part B7-Any other information in relation to sub-rule (2) of rule 114-I

Salary

SR. NO.

INFORMATION CODE

1

TDS-Ann.II-SAL

INFORMATION DESCRIPTION

Salary (TDS Annexure II)

INFORMATION SOURCE

HITACHI ASTEMO INDIA PRIVATE LIMITED (PNEF01495E)

COUNT

1

AMOUNT

10,69,432

SR. NO.



GROSS SALARY U/S 17(1)

VALUE OF PERQUISITES U/S
17(2)

PROFITS IN LIEU OF SALARY
U/S 17(3)

GROSS SALARY STATUS

1

01/04/2024

31/03/2025

10,69,432

0

0

10,69,432 Active

Part B3-Information relating to payment of taxes

SR. NO. ASSESSMENT
YEAR

MAJOR HEAD

MINOR HEAD

TAX (A)

SURCHARGE (B)

EDUCATION
CESS (C)

OTHERS (D)

TOTAL (A+B+C
+D)

BSR CODE

DEPOSIT

CHALLAN
SERIAL
NUMBER

CHALLAN IDENTIFICATION NUMBER

No Transactions Present

Note - If there is variation between the details of tax paid as displayed in Form26AS on TRACES portal and the information relating to tax payment as displayed in AIS on Compliance Portal, the taxpayer may rely on
the information displayed on TRACES portal for the purpose of filing of tax return and for other tax compliance purposes.

Part B4-Information relating to demand and refund

Refund

SR. NO.

ASSESSMENT YEAR

1

2024-25

MODE

ECS

NATURE OF REFUND

REFUND AMOUNT


ECS (direct credit to bank account)

43,360

05/10/2024

Download ID : AGDPM8485G202510101820


IP Address : 152.56.15.211

Page 2 of 2


"""

result = extract_metadata_from_text(sample_ocr_text)
print("\n🧾 Extracted Metadata:\n", result)
