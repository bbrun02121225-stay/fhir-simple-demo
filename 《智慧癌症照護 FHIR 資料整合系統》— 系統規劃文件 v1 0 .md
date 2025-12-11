# 《智慧癌症照護 FHIR 資料整合系統》— 系統規劃文件 v1.0.0

## **1. 情境敘述**

目前癌症病人的臨床資訊散落在不同系統，例如：

- **癌症登記長檔**
- **EMR 電子病歷紀錄**（含身高體重、血壓、脈搏、診斷、家族史等）
- **認知功能數據**（MMSE、LMI、DS、CTT、Stroop 等）
- **常規血液檢查資料**（WBC、Hb、Na/K、BUN、Cre、VitB12 等）

每個資料格式都不同、欄位名稱不一致、結構也不統一，導致：

1. 醫護人員難以完整掌握個案病情
2. 不同醫院間無法交換病人資訊
3. AI 模型因資料異質性過高，難以建立可靠預後或風險預測模型

因此需要一套**跨系統統一 FHIR 格式的資料整合平台**。

---

## **2. 情境目標**

### **2.1 要解決的問題**

- **各醫院資料格式不一致（欄位差異極大）**
- **資料散落在多個來源（癌登、EMR、LIS、問卷系統）**
    
    資料無法在單一視窗被查詢。
    
- **缺乏標準化格式，無法跨院使用或支援 AI 運算**
- **人工對欄位、治療史、檢驗資料進行比對耗時且容易錯誤**

### **2.2 系統目標**

- 建立**跨院共通的 FHIR 資料模型**
    - Patient
    - Observation（血壓、脈搏、血液檢驗、認知量表）
    - Condition（癌症診斷）
    - Procedure（手術、放療、化療）
    - MedicationStatement / MedicationRequest（抗癌藥物）
- 讓醫護人員可在**單一畫面看到所有系統資料**
- 大幅降低資料清洗時間，提升可讀性
- 讓 AI / ML 模型可直接吃 FHIR 結構化資料，提升分析品質
- 支援跨院查詢（未來可延伸至 FHIR server-to-server exchange）

---

## **3. 需求分析**

### **3.1 病人資料整合**

- 可以查詢病人的基本資料（生日、性別、身高、體重）

### **3.2 量測資料查詢**

- 可以看到病人的血壓、脈搏、血液檢驗（WBC/Hb/BUN/Cre/VitB12 等）
- 可以看到認知功能相關測試（MMSE、CTT、Stroop…）

### **3.3 癌症診斷與治療資訊整合**

- 要看到癌症診斷（ICD codes、分期、腫瘤大小等）
- 要看到手術、化療、副作用、放療資訊

### **3.4 跨資料表串聯**

- 按病人 UUID 自動把不同系統資料組合起來

### **3.5 FHIR 檔案匯出**

- 系統可以把所有資訊轉成標準 FHIR JSON

---

## **4. 工作流程**

### **4.1 系統運作流程**

1. **病人產生 UUID**
    
    所有資料來源（認知、血液、EMR、癌登）都會使用相同的 UUID。
    
2. **系統讀取資料來源**
    - 認知功能表：MMSE、LMI、Stroop 等分數
    - 血液檢驗表：WBC、Hb、Na/K、BUN、Cre、VitB12 等
    - EMR：身高體重、血壓、家族史、診斷
    - 癌登資料：腫瘤大小、分期、治療、復發狀態
3. **系統將資料轉換成 FHIR Resource**
    - 身高體重 → Observation
    - 血壓、脈搏 → Observation
    - 認知測試 → Observation
    - 癌症診斷 → Condition
    - 手術、化療、副作用 → Procedure / MedicationStatement
4. **系統自動打包成一份完整的 FHIR Bundle**
    
    內含 Patient、Observation、Condition、Procedure、Medication 等資料。
    
5. **使用者在瀏覽器看到整合界面：**
    - 基本資料
    - 檢驗趨勢
    - 認知功能趨勢
    - 癌症診斷與治療時間軸
6. **資料可以被 Github、FHIR Server 或其他醫院讀取**

---

## **5. 使用角色**

- **病人**：提供個人資料與問卷
- **護理師**：紀錄基本生命徵象、量測資料
- **醫師**：查詢所有整合後的 FHIR 病歷資料
- **資料工程師**：維護 FHIR Mapping 與格式轉換
- **研究者 / AI 工程師**：使用標準化資料進行分析、建模

---

## **6. 主要 FHIR Resource**

### **6.1 Patient（病人基本資料）**

- UUID
- 性別（0/1）
- 生日（yyyy/mm）

---

### **6.2 Observation（最重要：所有量測都能統一轉換）**

### **【生命徵象】**

- 身高 Height
- 體重 Weight
- 收縮壓 / 舒張壓
- 脈搏 Heart rate

### **【常規血液檢測】**

- GOT/AST, GPT/ALT
- WBC, Hb, Plt
- Na, K
- BUN, Cre
- VitB12, Folate

### **【認知功能量表】**

- MMSE
- LMI, LMII
- DS
- CTT-1 / CTT-2
- Stroop W/C/CW

---

### **6.3 Condition**

- ICD-10 診斷
- 癌別（如 DLBCL C833、Burkitt C837）
- 腫瘤大小、分期（TNM），來源於癌登長檔

---

### **6.4 Procedure**

- 手術方式（如 4.1.4 Surgical Procedure）
- 放射治療技術（EBRT, CTV dose 等）
    
    來源：癌登長檔
    

---

### **6.5 MedicationStatement / MedicationRequest**

- 藥物名稱
- 劑量
- 頻次

---

### **6.6 QuestionnaireResponse**

來源：EMR 問卷

---

# **（附）FHIR 實作內容產出建議**

---

## **A. 資料規格文件**

```
- Patient.fhir.json
- Observation-lab.fhir.json
- Observation-vitalSigns.fhir.json
- Observation-cognitive.fhir.json
- Condition-cancer.fhir.json
- Procedure-surgery.fhir.json
- MedicationStatement-chemo.fhir.json
- Bundle-fullRecord.fhir.json
```

---

## **B. 程式碼（Python + Pandas → FHIR JSON）**

可加入以下模組：

- csv → DataFrame
- df → FHIR Resource mapping
- UUID → Resource.identifier
- 自動產生 Observation.code（LOINC 可加入）

---

## **C. 執行結果**

- FHIR Bundle（含全部 resource）
- FHIR Validator 驗證通過 screenshot

---

## **D. 延伸應用**

- 跨院 FHIR Server 查詢（HAPI FHIR）
- AI 預測模型（認知衰退／疾病進展）
- 時間序列視覺化（blood trend, cognition trend）

---

# **（附）學習紀錄文件建議大綱**

### **1. 教學影片觀看紀錄**

→ 寫你理解的 FHIR R4 結構、Patient/Observation/Condition 觀念

### **2. 與 AI 互動紀錄**

→ 截圖 ChatGPT 生成 mapping、FHIR 資料、schema 的過程

### **3. 與導師 weaver 的討論摘要**

→ 問題、修正點、mapping 優化

### **4.心得（至少 500 字）**

→ 禁止 AI 代寫，但我可以給你架構