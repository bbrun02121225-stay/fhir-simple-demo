# demo.py 使用說明（README） v1.0.0

本檔案 `demo.py` 是一支**教學／競賽 demo 用程式**，不依賴任何 CSV 或實際醫院資料，在程式中產生「假資料」，示範：

- 如何**組出 FHIR Resource（Patient、Observation）**
- 如何把 Resource **上傳到 FHIR Server**
- 如何再從 FHIR Server **把資料抓回來**
- 並用「人類看得懂的欄位文字」印出**送出的欄位**與**伺服器儲存後的欄位**

---

## 1. 執行環境需求

- Python 3.9+（建議）
- 已安裝套件：
  - `pandas`
  - `requests`

可以用下列指令安裝：

```bash
pip install pandas requests
```

---

## 2. FHIR Server 設定

程式預設使用：

- Base URL：  
  ```python
  BASE_URL = "http://203.64.84.177:8080/fhir"
  ```

若要改成其他 FHIR Server，只需要修改檔案開頭的 `BASE_URL` 即可。

---

## 3. 如何執行

### 3.1 從指定路徑直接執行

在 macOS 終端機（Terminal）中：

```bash
/usr/local/bin/python3 "/Users/dino_chen/Library/Mobile Documents/com~apple~CloudDocs/NCHC/inputfile/demo.py"
```

或先切到資料夾再執行：

```bash
cd "/Users/dino_chen/Library/Mobile Documents/com~apple~CloudDocs/NCHC/inputfile"
python3 demo.py
```

### 3.2 VSCode 中執行

1. 打開 `demo.py`
2. 右上角按「Run Python File」
3. 查看下方 TERMINAL 面板輸出

---

## 4. 程式主要功能概觀

### 4.1 假資料 Resource Builder

程式中定義了多個 helper function 用來組 FHIR Resource，其中 demo 目前實際用到的是：

- ```python
  build_patient(row) -> dict
  ```

  給一個簡單的 dict，例如：

  ```python
  patient_row = {
      "uuid": "DEMO-001",
      "gender": "1",          # 1 → male
      "birthDate": "1960-01-01"
  }
  ```

  就會組成一個 FHIR Patient resource。

- ```python
  build_vital_observation(row) -> list[dict]
  build_lab_observation(row)   -> dict
  build_cognitive_observation(row) -> dict
  build_condition(row) -> dict
  build_procedure(row) -> dict
  build_medication_statement(row) -> dict
  ```

> 註：目前 demo 的主流程只實際使用 `build_patient()`，  
> 其他 builder 是預留給之後要做 Bundle 或多 resource 範例用。

---

### 4.2 與 FHIR Server 溝通的函式

- `post_resource(resource: dict) -> dict`  
  將單一 Resource 透過 HTTP `POST` 上傳到 FHIR Server，例如：
  
  - POST `/Patient`
  - POST `/Observation`

- `get_resource(resource_type: str, resource_id: str) -> dict`  
  透過 HTTP `GET` 讀回指定 Resource，例如：

  - GET `/Patient/{id}`
  - GET `/Observation/{id}`

- `print_patient_summary(sent: dict, stored: dict)`  
  以文字方式印出 Patient：

  - 送出的欄位（identifier.value、gender、birthDate）
  - 伺服器儲存後的欄位（id、identifier.value、gender、birthDate）

- `print_observation_summary(sent: dict, stored: dict)`  
  以文字方式印出 Observation：

  - 送出的欄位（code.text、value、subject.reference、effectiveDateTime）
  - 伺服器儲存後的欄位（id、code.text、value、subject.reference、effectiveDateTime）

這些函式的目的就是讓 demo **不顯示 JSON 內容**，改用欄位對欄位的文字方式說明，比較適合給初學者或展示用。

---

### 4.3 Demo 主流程：`demo_upload_and_fetch()`

主流程函式：

```python
def demo_upload_and_fetch() -> None:
    ...
```

步驟說明：

1. **產生一筆假的 Patient 資料**

   ```python
   patient_row = {
       "uuid": "DEMO-001",
       "gender": "1",
       "birthDate": "1960-01-01"
   }
   patient_resource = build_patient(patient_row)
   ```

2. **把這個 Patient `POST` 到 FHIR Server**

   - URL：`{BASE_URL}/Patient`
   - Content-Type：`application/fhir+json`
   - Body：`patient_resource` 的 JSON

   成功後，Server 會回傳一個帶有 `id` 的 Patient resource。

3. **印出送出與儲存後的欄位**

   使用：

   ```python
   print_patient_summary(patient_resource, stored_patient)
   ```

   終端機輸出會類似：

   ```text
   === Patient（病人基本資料）===
   送出的欄位：
     identifier.value = DEMO-001
     gender           = male
     birthDate        = 1960-01-01

   伺服器儲存後的欄位：
     id               = 12345
     identifier.value = DEMO-001
     gender           = male
     birthDate        = 1960-01-01
   ```

4. **從 Server 再用 GET 讀回剛剛建立的 Patient**

   - 呼叫：

     ```python
     fetched_patient = get_resource("Patient", patient_id)
     ```

   - 以文字方式印出 `id / identifier.value / gender / birthDate`。

5. **產生一筆假的體重 Observation**

   使用前面拿到的 `patient_id` 當 subject：

   ```python
   observation_weight = {
       "resourceType": "Observation",
       "status": "final",
       "category": [...],
       "code": {...},           # Body weight
       "subject": {
           "reference": f"Patient/{patient_id}"
       },
       "effectiveDateTime": "2024-06-01T08:30:00+08:00",
       "valueQuantity": {
           "value": 70.5,
           "unit": "kg",
           "system": "http://unitsofmeasure.org",
           "code": "kg",
       },
   }
   ```

6. **把 Observation `POST` 到 FHIR Server**

   - URL：`{BASE_URL}/Observation`
   - Body：`observation_weight` 的 JSON

   成功後會取得一個 Observation 的 `id`。

7. **印出 Observation 的送出欄位與儲存欄位**

   使用：

   ```python
   print_observation_summary(observation_weight, stored_obs)
   ```

   終端機會類似：

   ```text
   === Observation（量測資料）===
   送出的欄位：
     code.text        = Body weight
     value            = 70.5 kg
     subject.reference= Patient/12345
     effectiveDateTime= 2024-06-01T08:30:00+08:00

   伺服器儲存後的欄位：
     id               = 67890
     code.text        = Body weight
     value            = 70.5 kg
     subject.reference= Patient/12345
     effectiveDateTime= 2024-06-01T08:30:00+08:00
   ```

8. **再用 GET 讀回 Observation**

   - 呼叫：

     ```python
     fetched_obs = get_resource("Observation", obs_id)
     ```

   - 以文字方式印出 `id / code.text / value / subject.reference / effectiveDateTime`。

---

## 5. `main()` 入口點

程式最後的入口如下：

```python
def main():
    # Demo：直接用程式內建的假資料示範「上資料」與「拿資料」
    demo_upload_and_fetch()


if __name__ == "__main__":
    main()
```

也就是說，直接執行：

```bash
python demo.py
```

時，會跑 `demo_upload_and_fetch()`，完成完整的「上資料 + 拿資料」示範。

---

## 6. 可延伸／客製化的方向

你可以以這支 demo 為基礎，做以下延伸：

1. **增加更多 Resource 的 demo**
   - 呼叫 `build_condition()` 建立癌症診斷 Condition
   - 呼叫 `build_lab_observation()` 送 Hb、WBC 等 lab 資料
   - 再用 `post_resource()` / `get_resource()` 做完整 CRUD 示範

2. **改為讀 CSV / DB 再產生 Resource**
   - 把原來 `build_bundle()` 中的設計接回來
   - 由多個 DataFrame 組出一包 `Bundle`，再 `POST` 到 FHIR Server

3. **在競賽簡報中使用**
   - 直接把終端機畫面截圖，當作「實際與 FHIR Server 互動」的證據
   - 搭配 README 內容說明「送出的欄位 vs. 回來的欄位」，讓評審不需要懂 JSON 也能理解。

---

## 7. 版本資訊

- 版本：v1.0.0
- 說明：
  - 初版 README，對應目前 `demo.py` 實作：
    - Patient + Observation 的上傳與查詢 demo
    - 不依賴外部輸入檔案
    - 結果輸出採人類可讀格式（非 JSON dump）