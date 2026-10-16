---
target: proj-stack-overflow-auto-tagging
status: draft
---

# Stack Overflow Auto-Tagging

## Problem
Tags drive search and discoverability on Stack Overflow, but manual tags are often inconsistent or missing. The project predicts multiple relevant tags for a question automatically.

## Models
Three approaches were compared on 100K+ questions: a Hidden Markov Model written from scratch with Viterbi decoding over learned emission and transition probabilities (68.4% micro-F1), a TF-IDF Logistic Regression classifier using one-vs-rest (a classical baseline), and a fine-tuned DistilBERT (85% micro-F1).

## Evaluation metrics
Each model was measured on precision at k, recall at k, F1, Jaccard similarity, exact match ratio and Hamming loss, along with training and inference time, so the comparison covers both accuracy and cost.

## Confidence filtering
Predicted tags are filtered by adjustable probability thresholds, so the system returns only tags it is reasonably confident about rather than a fixed number.

## Interactive app
A live demo built with Streamlit lets you pick a model and get tag predictions in real time. Models can run locally or be fetched from the Hugging Face Hub, and the app is deployed at stackoverflow-tagging-system.streamlit.app.

## Team
Built by a team of three.

## Taniksha's part
TODO
