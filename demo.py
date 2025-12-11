import pandas as pd
import json
from datetime import datetime
import requests

BASE_URL = "http://203.64.84.177:8080/fhir"


# 輔助：UUID → Patient resource id

def patient_id_from_uuid(uuid: str) -> str:
    return f"pat-{uuid}"


def condition_id_from_uuid(uuid: str) -> str:
    return f"cond-{uuid}"


# Resource builders

def build_patient(row) -> dict:
    gender_map = {"M": "male", "F": "female", "0": "female", "1": "male"}
    gender = gender_map.get(str(row["gender"]), "unknown")

    return {
        "resourceType": "Patient",
        "id": patient_id_from_uuid(row["uuid"]),
        "identifier": [
            {
                "system": "https://example.org/uuid",
                "value": row["uuid"],
            }
        ],
        "gender": gender,
        "birthDate": str(row["birthDate"]),
    }


def build_lab_observation(row) -> dict:
    # 實務上可對 test_name 做 LOINC 對應，目前先用 local-lab system
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "https://example.org/fhir/CodeSystem/local-lab",
                    "code": row["test_name"],
                    "display": row["test_name"],
                }
            ],
            "text": row["test_name"],
        },
        "subject": {
            "reference": f"Patient/{patient_id_from_uuid(row['uuid'])}"
        },
        "effectiveDateTime": f"{row['date']}T00:00:00+08:00",
        "valueQuantity": {
            "value": float(row["value"]),
            "unit": row["unit"],
            "system": "http://unitsofmeasure.org",
        },
    }


def build_vital_observation(row) -> list:
    """回傳多個 Observation：血壓、脈搏、身高、體重。"""

    resources: list[dict] = []

    patient_ref = f"Patient/{patient_id_from_uuid(row['uuid'])}"
    eff_dt = f"{row['date']}T00:00:00+08:00"

    # 血壓
    bp = {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "85354-9",
                    "display": "Blood pressure panel",
                }
            ],
            "text": "Blood pressure",
        },
        "subject": {"reference": patient_ref},
        "effectiveDateTime": eff_dt,
        "component": [],
    }

    if pd.notna(row.get("systolic")):
        bp["component"].append(
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8480-6",
                            "display": "Systolic blood pressure",
                        }
                    ]
                },
                "valueQuantity": {
                    "value": float(row["systolic"]),
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]",
                },
            }
        )

    if pd.notna(row.get("diastolic")):
        bp["component"].append(
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8462-4",
                            "display": "Diastolic blood pressure",
                        }
                    ]
                },
                "valueQuantity": {
                    "value": float(row["diastolic"]),
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]",
                },
            }
        )

    if bp["component"]:
        resources.append(bp)

    # 脈搏
    if pd.notna(row.get("heart_rate")):
        resources.append(
            {
                "resourceType": "Observation",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8867-4",
                            "display": "Heart rate",
                        }
                    ],
                    "text": "Heart rate",
                },
                "subject": {"reference": patient_ref},
                "effectiveDateTime": eff_dt,
                "valueQuantity": {
                    "value": float(row["heart_rate"]),
                    "unit": "beats/min",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min",
                },
            }
        )

    # 身高
    if pd.notna(row.get("height")):
        resources.append(
            {
                "resourceType": "Observation",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8302-2",
                            "display": "Body height",
                        }
                    ],
                    "text": "Body height",
                },
                "subject": {"reference": patient_ref},
                "effectiveDateTime": eff_dt,
                "valueQuantity": {
                    "value": float(row["height"]),
                    "unit": "cm",
                    "system": "http://unitsofmeasure.org",
                    "code": "cm",
                },
            }
        )

    # 體重
    if pd.notna(row.get("weight")):
        resources.append(
            {
                "resourceType": "Observation",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "29463-7",
                            "display": "Body weight",
                        }
                    ],
                    "text": "Body weight",
                },
                "subject": {"reference": patient_ref},
                "effectiveDateTime": eff_dt,
                "valueQuantity": {
                    "value": float(row["weight"]),
                    "unit": "kg",
                    "system": "http://unitsofmeasure.org",
                    "code": "kg",
                },
            }
        )

    return resources


def build_cognitive_observation(row) -> dict:
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "survey",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "https://example.org/fhir/CodeSystem/cognitive-test",
                    "code": row["test_type"],
                    "display": row["test_type"],
                }
            ],
            "text": row["test_type"],
        },
        "subject": {
            "reference": f"Patient/{patient_id_from_uuid(row['uuid'])}"
        },
        "effectiveDateTime": f"{row['date']}T00:00:00+08:00",
        "valueInteger": int(row["score"]),
    }


def build_condition(row) -> dict:
    return {
        "resourceType": "Condition",
        "id": condition_id_from_uuid(row["uuid"]),
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                }
            ]
        },
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": row["icd10"],
                    "display": row.get("display", row["icd10"]),
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id_from_uuid(row['uuid'])}"
        },
        "onsetDateTime": str(row["diagnosis_date"]),
    }


def build_procedure(row) -> dict:
    return {
        "resourceType": "Procedure",
        "status": "completed",
        "code": {
            "coding": [
                {
                    "system": "https://example.org/fhir/CodeSystem/surgery",
                    "code": row["code"],
                    "display": row["display"],
                }
            ],
            "text": row["display"],
        },
        "subject": {
            "reference": f"Patient/{patient_id_from_uuid(row['uuid'])}"
        },
        "performedDateTime": str(row["date"]),
    }


def build_medication_statement(row) -> dict:
    return {
        "resourceType": "MedicationStatement",
        "status": "completed",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "https://example.org/fhir/CodeSystem/chemo-drug",
                    "code": row["regimen"],
                    "display": row["regimen"],
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id_from_uuid(row['uuid'])}"
        },
        "effectivePeriod": {
            "start": str(row["start_date"]),
            "end": str(row["end_date"]),
        },
        "dosage": [
            {
                "text": row.get("note", ""),
            }
        ],
    }


# -------------------------
# 與 FHIR Server 溝通的輔助函式
# -------------------------

def post_resource(resource: dict) -> dict:
    """將單一 FHIR Resource POST 到 FHIR Server，回傳 Server 儲存後的 Resource JSON。"""
    url = f"{BASE_URL}/{resource['resourceType']}"
    headers = {"Content-Type": "application/fhir+json;charset=utf-8"}
    resp = requests.post(url, headers=headers, data=json.dumps(resource))
    resp.raise_for_status()
    return resp.json()


def get_resource(resource_type: str, resource_id: str) -> dict:
    """從 FHIR Server 讀取單一 Resource。"""
    url = f"{BASE_URL}/{resource_type}/{resource_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def print_patient_summary(sent: dict, stored: dict) -> None:
    """以人類可讀格式印出送出的 Patient 欄位與儲存後的欄位。"""
    print("=== Patient（病人基本資料）===")
    print("送出的欄位：")
    print(f"  identifier.value = {sent['identifier'][0]['value']}")
    print(f"  gender           = {sent.get('gender')}")
    print(f"  birthDate        = {sent.get('birthDate')}")

    print("\n伺服器儲存後的欄位：")
    print(f"  id               = {stored.get('id')}")
    print(f"  identifier.value = {stored.get('identifier', [{}])[0].get('value')}")
    print(f"  gender           = {stored.get('gender')}")
    print(f"  birthDate        = {stored.get('birthDate')}")
    print()


def print_observation_summary(sent: dict, stored: dict) -> None:
    """以人類可讀格式印出送出的 Observation 欄位與儲存後的欄位。"""
    print("=== Observation（量測資料）===")
    print("送出的欄位：")
    print(f"  code.text        = {sent.get('code', {}).get('text')}")
    if "valueQuantity" in sent:
        print(f"  value            = {sent['valueQuantity'].get('value')} {sent['valueQuantity'].get('unit')}")
    print(f"  subject.reference= {sent.get('subject', {}).get('reference')}")
    print(f"  effectiveDateTime= {sent.get('effectiveDateTime')}")

    print("\n伺服器儲存後的欄位：")
    print(f"  id               = {stored.get('id')}")
    print(f"  code.text        = {stored.get('code', {}).get('text')}")
    vq = stored.get('valueQuantity')
    if isinstance(vq, dict):
        print(f"  value            = {vq.get('value')} {vq.get('unit')}")
    print(f"  subject.reference= {stored.get('subject', {}).get('reference')}")
    print(f"  effectiveDateTime= {stored.get('effectiveDateTime')}")
    print()


# -------------------------
# Demo：用假資料上 / 下 FHIR Server
# -------------------------

def demo_upload_and_fetch() -> None:
    # 1. 準備一筆假的病人資料
    patient_row = {
        "uuid": "DEMO-001",
        "gender": "1",            # 1 → male（在 build_patient 裡會轉換）
        "birthDate": "1960-01-01"
    }
    patient_resource = build_patient(patient_row)

    print(">>> 準備送出的 Patient（病人）Resource")
    print(f"resourceType      = {patient_resource['resourceType']}")
    print(f"identifier.value  = {patient_resource['identifier'][0]['value']}")
    print(f"gender            = {patient_resource['gender']}")
    print(f"birthDate         = {patient_resource['birthDate']}")
    print()

    # 2. 將 Patient 上傳到 FHIR Server
    stored_patient = post_resource(patient_resource)
    patient_id = stored_patient.get("id")
    print_patient_summary(patient_resource, stored_patient)

    # 3. 再呼叫一次 GET，示範如何「拿資料」
    fetched_patient = get_resource("Patient", patient_id)
    print("=== 再次從 Server 讀回 Patient（GET）===")
    print(f"  id               = {fetched_patient.get('id')}")
    print(f"  identifier.value = {fetched_patient.get('identifier', [{}])[0].get('value')}")
    print(f"  gender           = {fetched_patient.get('gender')}")
    print(f"  birthDate        = {fetched_patient.get('birthDate')}")
    print()

    # 4. 準備一筆假的體重 Observation，直接用剛剛建立好的 Patient.id 做 reference
    observation_weight = {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "29463-7",
                    "display": "Body weight",
                }
            ],
            "text": "Body weight",
        },
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

    print(">>> 準備送出的 Observation（體重）Resource")
    print(f"resourceType      = {observation_weight['resourceType']}")
    print(f"code.text         = {observation_weight['code']['text']}")
    print(f"value             = {observation_weight['valueQuantity']['value']} {observation_weight['valueQuantity']['unit']}")
    print(f"subject.reference = {observation_weight['subject']['reference']}")
    print()

    # 5. 將 Observation 上傳到 FHIR Server
    stored_obs = post_resource(observation_weight)
    obs_id = stored_obs.get("id")
    print_observation_summary(observation_weight, stored_obs)

    # 6. 再用 GET 把 Observation 讀回來
    fetched_obs = get_resource("Observation", obs_id)
    print("=== 再次從 Server 讀回 Observation（GET）===")
    print(f"  id               = {fetched_obs.get('id')}")
    print(f"  code.text        = {fetched_obs.get('code', {}).get('text')}")
    vq = fetched_obs.get("valueQuantity")
    if isinstance(vq, dict):
        print(f"  value            = {vq.get('value')} {vq.get('unit')}")
    print(f"  subject.reference= {fetched_obs.get('subject', {}).get('reference')}")
    print(f"  effectiveDateTime= {fetched_obs.get('effectiveDateTime')}")
    print()


# -------------------------
# 主流程：組 Bundle
# -------------------------

def build_bundle(patient_df, lab_df, vital_df, cog_df, cancer_df, surg_df, chemo_df) -> dict:
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [],
    }

    # Patient
    for _, row in patient_df.iterrows():
        pat = build_patient(row)
        bundle["entry"].append({"resource": pat})

    # Condition
    for _, row in cancer_df.iterrows():
        cond = build_condition(row)
        bundle["entry"].append({"resource": cond})

    # Lab
    for _, row in lab_df.iterrows():
        obs = build_lab_observation(row)
        bundle["entry"].append({"resource": obs})

    # Vital
    for _, row in vital_df.iterrows():
        obs_list = build_vital_observation(row)
        for obs in obs_list:
            bundle["entry"].append({"resource": obs})

    # Cognitive
    for _, row in cog_df.iterrows():
        obs = build_cognitive_observation(row)
        bundle["entry"].append({"resource": obs})

    # Surgery
    for _, row in surg_df.iterrows():
        proc = build_procedure(row)
        bundle["entry"].append({"resource": proc})

    # Chemo
    for _, row in chemo_df.iterrows():
        med = build_medication_statement(row)
        bundle["entry"].append({"resource": med})

    return bundle



def main():
    # Demo：直接用程式內建的假資料示範「上資料」與「拿資料」
    demo_upload_and_fetch()


if __name__ == "__main__":
    main()
