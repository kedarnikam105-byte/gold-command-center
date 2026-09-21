# 🥇 Gold Command Center

Multi-Agent AI Trading Dashboard for Gold (XAUUSD)

## Features

- **3 Specialist Analyst Agents**
  - Technical Analyst
  - Fundamental Analyst
  - Sentiment Analyst
- **Chief Officer** that makes the final Buy / Sell / Hold decision
- Live Gold price from Yahoo Finance
- Beautiful mobile + desktop dashboard
- Click any agent to see full analysis
- Daily activity log

## How to Run (Computer + Mobile)

### 1. Install Python packages

Open terminal and run:

```bash
cd gold_command_center
pip install -r requirements.txt
```

### 2. Add your Groq API Key

Create a file named `.env` in the same folder:

```
GROQ_API_KEY=gsk_your_key_here
```

(Paste the key I already received from you)

### 3. Start the app

```bash
streamlit run app.py
```

It will open in your browser automatically.

### 4. Use on Mobile

- Make sure your phone is on the same Wi-Fi as the computer
- Streamlit will show a Network URL like `http://192.168.x.x:8501`
- Open that URL on your phone browser
- It works as a mobile-friendly web app

You can also deploy it later to Streamlit Community Cloud (free) so it is always online.

## Important Notes

- This is for **education and research** only
- Never risk real money without thorough paper trading
- Free Groq models have rate limits — don’t spam the “Run Analysis” button
- Gold data comes from Yahoo Finance (GC=F futures)

## Project Structure

```
gold_command_center/
├── app.py                 ← Main dashboard
├── market_data.py         ← Live gold price
├── agents/
│   ├── base.py
│   └── analysts.py
├── logs/                  ← Saved analysis history
├── requirements.txt
└── README.md
```
