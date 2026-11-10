---
language: [tr]
license: apache-2.0
pipeline_tag: token-classification
base_model: ytu-ce-cosmos/modernbert-tr-base
library_name: transformers
tags: [kvkk, pii, ner, privacy, turkish, werea]
datasets: [Werea-co/Werea-KVKK-Bench]
---
# Werea-KVKK-PII-150M v2

Research-preview Turkish PII recogniser for the Werea KVKK PrivacyOps project.
It is trained for these synthetic span categories: ADDRESS, BIOMETRIC_DATA, CRIMINAL_CONVICTION_SECURITY, CREDIT_CARD, DATE_OF_BIRTH, DEVICE_ID, EMAIL, FINANCIAL_DATA, GENETIC_DATA, HEALTH_DATA, IBAN_TR, IPV4, PASSPORT_TR, PERSON, PHONE_TR, POLITICAL_OPINION, RELIGION, SEXUAL_LIFE, TCKN, UNION_MEMBERSHIP, VEHICLE_PLATE_TR.
The public training set is deterministic and entirely synthetic; it contains no
customer records. Use the deterministic rules layer for checksummed identifiers
and evaluate every category on an institution-specific, lawyer-reviewed corpus
before production deployment.

Validation F1 on the synthetic split: **1.0000**.
This score must not be interpreted as real-world compliance performance.

The model cannot determine legal compliance or choose a legal basis. Human
review is mandatory. See the dataset card and Werea PrivacyOps documentation.
