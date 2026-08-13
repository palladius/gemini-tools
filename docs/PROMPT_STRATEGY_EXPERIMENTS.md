# 🔬 Prompt Strategy Experiment Report (Kate Reference Binding)

## 📌 Executive Summary
Evaluation of 3 prompt strategies across 9 candidates for character consistency, using explicit reference image binding (Images A, B, C).

---

## 📊 Strategy Benchmark Results

| Strategy | Prompt Approach | Compressed AI Likeness Score (1-10 Scale) | Summary Verdict |
| :--- | :--- | :---: | :--- |
| **Strategy 1** | Explicit A/B/C Reference Binding & Anti-Beautification | **6.5 / 10** | 🟢 **Good**: Preserved ash-blonde hair tone, smile dimples, and nose bridge. |
| **Strategy 2** | Negative Constraints (`NO model skin`, `NO altered nose`) | **3.6 / 10** | ❌ **Poor**: Caused feature drift (hazel eyes, modified bone structure). |
| **Strategy 3** | Biometric Feature Blueprint | **6.5 / 10** | 👑 **Optimal**: High multi-angle fidelity and natural skin texture. |

---

## 📂 Candidate Summary

- **Strategy 1 Candidates**: `out/kate_exp1_cand1.png`, `out/kate_exp1_cand2.png`, `out/kate_exp1_cand3.png`
- **Strategy 2 Candidates**: `out/kate_exp2_cand1.png`, `out/kate_exp2_cand2.png`, `out/kate_exp2_cand3.png`
- **Strategy 3 Candidates**: `out/kate_exp3_cand1.png`, `out/kate_exp3_cand2.png`, `out/kate_exp3_cand3.png`

---

## 💡 Key Finding
Positive biometric feature blueprinting (Strategy 3) and explicit reference binding (Strategy 1) outperform negative prompt constraints (Strategy 2) for identity preservation.
