# Run Guide: Chatbot Final Optimized

## 1. Environment Setup

From `project/`:

```powershell
"c:/Users/dayab/UofT/WINTER 2026/MIE1624H Intro to Data/course project/EXECUTION/project/.venv/Scripts/python.exe" -m pip install -r chatbot_final_optimized/requirements.txt
```

## 2. Run Streamlit Dashboard App

From `project/`:

```powershell
streamlit run chatbot_final_optimized/app/dashboard_app.py
```

If `streamlit` is not on PATH, use:

```powershell
"c:/Users/dayab/UofT/WINTER 2026/MIE1624H Intro to Data/course project/EXECUTION/project/.venv/Scripts/python.exe" -m streamlit run chatbot_final_optimized/app/dashboard_app.py
```

## 3. Optional Static Export Helpers

```powershell
"c:/Users/dayab/UofT/WINTER 2026/MIE1624H Intro to Data/course project/EXECUTION/project/.venv/Scripts/python.exe" chatbot_final_optimized/app/dashboard_overview_copy.py
"c:/Users/dayab/UofT/WINTER 2026/MIE1624H Intro to Data/course project/EXECUTION/project/.venv/Scripts/python.exe" chatbot_final_optimized/app/dashboard_timeline_copy.py
```

## 4. Smoke Test (Data Loader)

```powershell
"c:/Users/dayab/UofT/WINTER 2026/MIE1624H Intro to Data/course project/EXECUTION/project/.venv/Scripts/python.exe" -c "from pathlib import Path; from chatbot_final_optimized.src.dashboard.load_dashboard_data import load_dashboard_data; b=load_dashboard_data(Path('chatbot_final_optimized')); print('frames',len(b.frames)); print('unresolved',len(b.unresolved)); print('scenario', 'scenario_comparison.csv' in b.frames)"
```

Expected: non-zero loaded frames, scenario table available, and a short unresolved list containing optional references.
