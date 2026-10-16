---
target: proj-break-the-bot
status: draft
---

# Break The Bot

## Problem
LLMs deployed in products stay vulnerable to jailbreaks and prompt injection. Break The Bot treats safety evaluation as a continuous pipeline that runs adversarial prompts against models and scores the responses automatically, instead of one-off manual red-teaming.

## Pipeline
One Airflow DAG runs the whole flow: pull versioned data with DVC, preprocess the SALAD adversarial prompt set, validate it with Great Expectations, enforce the validation policy, generate responses from the target models, score them with an LLM judge, then compute metrics and bias detection in parallel, push the outputs back with DVC and email a summary.

## Data quality gates
A validation step builds a baseline schema and checks every run against it. It writes run statistics (row count, nulls, duplicates, unknown category rate, text length range) and an anomalies report split into hard failures, soft warnings and info. Hard failures stop the pipeline before any model is called, so bad data fails fast instead of producing misleading safety numbers.

## Judging and metrics
An LLM-as-a-Judge running Llama 3.3 on Groq scores each response for safety and refusal quality. The pipeline reports attack success rate, over-refusal and coverage across prompt categories, and a bias detection step slices results by category to find where attacks succeed disproportionately.

## Versioning and infrastructure
DVC with a Google Cloud Storage remote versions the processed data, model responses, judgements and metrics. The pipeline runs on Google Cloud Composer with Terraform-provisioned infrastructure, and metrics are served by a FastAPI service on Cloud Run, deployed through Cloud Build, feeding a live Streamlit dashboard.

## Alerts
Every run emails a validation report. Successful runs email validation and model metrics tables, and failures send stage-specific emails, using Airflow trigger rules so a skipped task is not reported as a failure.

## Team
Break The Bot was built by a team of six.

## Taniksha's part
TODO
