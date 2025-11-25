# Data Collection and Sentiment Analysis Pipeline

This folder contains scripts to collect YouTube transcripts for specific products and analyze their sentiment using the NVIDIA API.

## Prerequisites

- Python 3.8+
- A valid NVIDIA API Key
- A `cookies.txt` file for YouTube authentication

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r ../requirements.txt
   pip install openai python-dotenv
   ```
   *(Note: `openai` and `python-dotenv` are required for the sentiment analysis script)*

## Configuration

### 1. NVIDIA API Key
The sentiment analysis script uses NVIDIA's API (Llama 3.1 405B).

1. Go to [NVIDIA NIM](https://build.nvidia.com/explore).
2. Generate an API key.
3. Create a `.env` file in the root of the project (`../.env`).
4. Add your key to the file:
   ```env
   NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### 2. YouTube Cookies (`cookies.txt`)
To avoid bot detection and access transcripts reliably, `yt-dlp` requires a cookies file.

1. Install a browser extension to export cookies (e.g., "Get cookies.txt LOCALLY" for Chrome/Firefox).
2. Go to [YouTube](https://www.youtube.com) and ensure you are logged in.
3. Use the extension to export your cookies as `cookies.txt`.
4. Place the `cookies.txt` file in the **project root directory** (preferred) or the `data_collector` directory.

## Usage

### Step 1: Collect Data
Run the data collector to search for videos and download transcripts.
```bash
python data_collector/collect_data.py
```
This will:
- Search for videos related to the products defined in the script.
- Download transcripts to `data_collector/temp_transcripts/`.
- Save consolidated data to `data_collector/data/`.

### Step 2: Analyze Sentiment
Run the sentiment analysis script to process the collected transcripts.
```bash
python data_collector/analyze_sentiment.py
```
This will:
- Read the collected transcripts.
- Send them to the NVIDIA API for analysis.
- Save the sentiment results to `data_collector/sentiment_data/`.

## Output Structure

- `data/`: Contains raw transcript data JSONs.
- `sentiment_data/`: Contains the analysis results (sentiment scores, pros/cons, summaries).
