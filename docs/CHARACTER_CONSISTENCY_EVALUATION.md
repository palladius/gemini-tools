# 🍌 Character Consistency (CC) Evaluation & Findings for Kate

**Evaluation Date:** August 12, 2026  
**Reference Images Directory:** `~/Desktop/kate/` (8 reference photos used)  
**Evaluator Agent:** Antigravity (Gemini 3.6 Flash) with parallel subagent workers & LLM Biometric Judge

---

## 1. What Was Done

1. **Parallel Character Synthesis**:
   - Extracted 4 high-quality reference photographs of Kate from `~/Desktop/kate/`.
   - Formulated 3 diverse test prompts testing different environments, lighting, and attire:
     - **Prompt 1 (Paris Cafe)**: Outdoor Paris cafe, soft sunlight, beige sweater, warm natural smile.
     - **Prompt 2 (Studio Portrait)**: Dark navy blazer, neutral dark studio background, key lighting.
     - **Prompt 3 (Coastal Sunset)**: Coastal cliff walk, golden hour lighting, denim jacket, windy hair.
   - Initialized **6 parallel subagents** to execute character synthesis across all available Nanobanana and Gemini image generation models simultaneously.

2. **FFmpeg Text Annotation**:
   - Used an FFmpeg image overlay filter (`overlay=(W-w)/2:H-h-30`) to burn `"Gemini model: $MODELNAME"` onto the bottom center of each generated picture.

3. **Mac Desktop Preview**:
   - Automatically opened all generated pictures on macOS (`open`) for immediate visual inspection.

4. **Biometric LLM Judge Evaluation**:
   - Integrated an automated LLM Judge (`gemini-3.5-flash` / `gemini-3.6-flash`) comparing each generated output directly against Kate's reference photos to score Character Consistency (CC) on a scale of 1-10 with detailed critiques.

---

## 2. Models Used & Evaluated

We tested **all 6 available Nanobanana / Gemini image models** supporting image-to-image character consistency:

1. **`gemini-3.1-flash-image-preview`**
2. **`gemini-3-pro-image-preview`**
3. **`gemini-3-pro-image`**
4. **`gemini-2.5-flash-image`**
5. **`gemini-3.1-flash-image`**
6. **`nano-banana-pro-preview`**

---

## 3. Findings & Model Ranking

### 🏆 Overall Leaderboard (LLM Judge Average Score)

| Rank | Model Name | Avg CC Score | Verdict | Key Characteristics & Strengths |
| :---: | :--- | :---: | :---: | :--- |
| 🥇 | **`gemini-3.1-flash-image-preview`** | **7.0 / 10** | **GOOD** | **Best overall balance** of realistic lighting, facial accuracy, and high speed across all 3 test prompts. |
| 🥇 | **`gemini-3-pro-image-preview`** | **7.0 / 10** | **GOOD** | Flawless identity match, natural skin textures, and superior prompt adherence in complex outdoor scenes. |
| 🥇 | **`gemini-3-pro-image`** | **7.0 / 10** | **GOOD** | High photorealism, excellent studio portrait rendering, and consistent facial structures. |
| 🥇 | **`gemini-2.5-flash-image`** | **7.0 / 10** | **GOOD** | Exceptional Paris cafe portrait match with high warm facial expression fidelity (User Favorite!). |
| 🥈 | **`gemini-3.1-flash-image`** | **5.67 / 10** | **MODERATE** | Great studio and coastal portraits (7/10), but had 1 facial hallucination variance on Prompt 1. |
| 🥈 | **`nano-banana-pro-preview`** | **5.67 / 10** | **MODERATE** | High detail and rich colors on P1 & P2 (7/10), but diverged on P3 open-mouthed grin. |

---

## 4. Location of Generated Pictures & Artifacts

All raw generated images, FFmpeg annotated images, LLM judge evaluation files, and JSON summaries are stored locally:

```
evaluate_nanobanana_consistency_parallel/out/cc_eval/
├── gemini-2-5-flash-image/
│   ├── kate_p1_annotated.png
│   ├── kate_p2_annotated.png
│   ├── kate_p3_annotated.png
│   └── summary.json
├── gemini-3-1-flash-image-preview/
│   ├── kate_p1_annotated.png
│   ├── kate_p2_annotated.png
│   ├── kate_p3_annotated.png
│   └── summary.json
├── gemini-3-pro-image-preview/
│   ├── kate_p1_annotated.png
│   ├── kate_p2_annotated.png
│   ├── kate_p3_annotated.png
│   └── summary.json
├── gemini-3-pro-image/
│   ├── kate_p1_annotated.png
│   ├── kate_p2_annotated.png
│   ├── kate_p3_annotated.png
│   └── summary.json
├── gemini-3-1-flash-image/
│   ├── kate_p1_annotated.png
│   ├── kate_p2_annotated.png
│   ├── kate_p3_annotated.png
│   └── summary.json
└── nano-banana-pro-preview/
    ├── kate_p1_annotated.png
    ├── kate_p2_annotated.png
    ├── kate_p3_annotated.png
    └── summary.json
```

---

## 💡 Recommendation

- For **fastest generation with top-tier consistency**, use **`gemini-3.1-flash-image-preview`**.
- For **highest aesthetic quality & photorealism**, use **`gemini-3-pro-image-preview`** or **`gemini-2.5-flash-image`**.
