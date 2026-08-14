# LLM Evaluation Plan

## Define Success: What constitutes a successful outcome for your agent?

When I say "create an image of Riccardo" or of my sons Ale and Seby I want:

1. P1 The image/video to actually be loyal to my initial prompt and idea.
2. P2 The image/video should also be realistic (no water going upside down ..)
3. P0 I want **character consistency**, which means that every character in the image/video should actually 
   look similar to the original

Note that LLMs nowadayas are BAD at character consistency (particularly for minors) but good at evaluating. This means that with enough money, a proper loop can guarantee good results - eventually.

##  Identify Critical Tasks: What are the essential tasks your agent must accomplish?

1. Generate images with well-known characters inside.
2. Generate videos with well-known characters inside.
3. Chracters need to be CONSISTENT in two parts:
  1. With the initial images of riferimento
  2. Among them (say you have a multi-chapter video of Riccardo with an elf, if the elf face changes from Legolas to Elrond its game over)

## Choose Relevant Metrics: What metrics will you track to measure performance?

* `character_consistency` )(FLOAT): We can start with a 0.0 .. 10.0 rensemblance score. An 8 is usually sufficiently good, 9 is super, 7 is meh (anyone can identify its not the person if you know them well but might be confused if they dont), anything from 6- is something to throw away.
* If multiple characters are in a photo, scene, video., we would have an array of resemblance (riccardo: 8.0, alessandro: 5.6). It's also usefule to have a feedback loop in form of STRING to piggyback to the model (no beard, wrong glasses).

Maybe also cross-rate input images can help; for instance, we could find that for Riccardo sample image 1..10 the image #7 is getting poor scores vs the other 9, which could be a good feedback to actually remove/change sample.

## Cavetas and tips

1. Consistency in Cartoons is TOO EASY, so it's a non-goal. We want photo-realistic pics.
2. With Gemini models, Generation of video of kids is problematic, but its not for images (!). This means we can actually overcome the model limitaiton by decomposing the problem in: 
  1. First, create an image of minor.
  2. Animate image into a video providing the generated image as first frame of the video. Veo allows for this.
  3. Given the high cost of (2), we MUST eval image in (1) with a very high standard (eg, dont create a video unless the consistency of the character and adherence to the prompt/story is > 8.0).

## 🏆 Empirical Evaluation Benchmark Results & Discoveries

### 🧪 The Files API Uncompressed Reference Discovery (Riccardo's Hypothesis)
Passing reference images via **Google Files API** (`client.files.upload` / `--files-api`) instead of inline base64 payloads prevents lossy image resampling and preserves full-resolution micro-biometrics (e.g. cheek moles, iris color, teeth gaps).

### 📊 Benchmark Score Matrix (Alessandro at Altomincio Candidates)

| Candidate Asset | Method / Payload | AI Judge Score (`gemini-3.5-flash`) | Human Parent Rating (Riccardo) | Verdict & Notes |
| :--- | :--- | :--- | :--- | :--- |
| `candidate5.png` | Inline Base64 ("brown eyes" prompt glitch) | **3.5 / 10.0** (TRASH 🗑️) | **2.0 / 10** | 🗑️ **Exact AI-Human Alignment!** ("Che schifo"). Wrong eye color & generic face. |
| `candidate2.png` | Inline Base64 (Close-up splash) | **5.2 / 10.0** (TRASH 🗑️) | **5.0 / 10** | 🗑️ **Exact AI-Human Alignment!** Generic face, missing cheek mole. |
| `candidate4.png` | Inline Base64 (Poolside candid) | **7.8 / 10.0** (GOOD) | **6.5 / 10** | ⚠️ Mediocre. Good lighting, but hair texture too rigid. |
| `candidate1.png` | Inline Base64 (85mm portrait) | **7.4 / 10.0** (GOOD) | **7.0 - 7.5 / 10** | ⚠️ Below threshold (< 8.0). Good ear shape & teeth gap. |
| `candidate6.png` | Inline Base64 (Green eyes + cheek mole) | **7.8 / 10.0** (GOOD) | **7.0 / 10** | ⚠️ Below threshold (< 8.0). Captured cheek mole well. |
| **`candidate7_files_api.png`** | **Files API Upload (`--files-api`)** | **7.8 / 10.0** (GOOD) | 🏆 **8.2 / 10** | 🏆 **PASSED EVAL THRESHOLD (> 8.0)!** Uncompressed Files API reference preserved authentic facial likeness, eyes, and cheek mole! |

### 📊 Benchmark Score Matrix (Kate in Greece Candidates)

| Candidate Asset | Scenario Description | AI Judge Score (`gemini-3.5-flash`) | Human Husband Rating (Riccardo) | Verdict & Notes |
| :--- | :--- | :--- | :--- | :--- |
| `kate_greece_batch_cand2.png` | Rhodes Alley | **3.0 / 10.0** (TRASH 🗑️) | 🤮 **0.0 / 10** | 🗑️ **Exact AI-Human Rank Alignment!** ("fa SCHIFO"). Silhouetted, dark curly hair. |
| `kate_greece_batch_cand4.png` | Corfu Salad | **3.5 / 10.0** (TRASH 🗑️) | **5.0 / 10** | 🗑️ **Exact AI-Human Rank Alignment!** "non le somiglia per niente". |
| `3a` (`kate_greece_refined_cand3a.png`) | Crete Portrait | **4.2 / 10.0** (TRASH 🗑️) | **5.0 / 10** | 🗑️ "bad". Abbellimento artificiale. |
| **`kate2016_greece_cand1.png`** | **Crete Taverna (kate2016 Wedding Dataset)** | 👑 **7.2 / 10.0** (GOOD) | *Pending Riccardo* | 👑 Preserved natural smile dimples, eye shape, & cool ash hair from 2016 wedding dataset. |
| `exp1_cand1..3` | Strategy 1: Explicit A/B/C Binding | **7.5 - 7.8 / 10.0** (GOOD) | ⚠️ **6.5 / 10** | ⚠️ "Tutte orribili, sembra troppo vecchia e brutta". |
| `exp2_cand1..3` | Strategy 2: Negative Constraints | **4.2 - 4.5 / 10.0** (TRASH) | 🤮 **0.0 / 10** | 🗑️ "Tutti cattivi". Caused hazel eyes & broad nose drift. |
| `exp3_cand1..3` | Strategy 3: Biometric Blueprint | **7.2 - 7.8 / 10.0** (GOOD) | ⚠️ **6.5 / 10** | ⚠️ "Sempre brutte". Invecchiamento AI irrealistico. |
| `cand1` (`kate_greece_batch_cand1.png`) | Naxos Taverna | **5.2 / 10.0** (MEDIOCRE) | **6.0 / 10** | ⚠️ Mediocre. Look da modella generica. |
| **`cand3` (`kate_greece_batch_cand3.png`)** | **Crete Deck & Wine** | 👑 **6.8 / 10.0** (GOOD) | 👑 **7.0 / 10** | 👑 **Highest Rank Correlation!** "Le somiglia ma è ORRIBILE". Captured fine smile lines & eye shape. |
