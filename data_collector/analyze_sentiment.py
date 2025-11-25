import json
import os
import glob
import logging
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configure the NVIDIA API client
# Ensure NVIDIA_API_KEY is set in your environment variables
client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = os.environ.get("NVIDIA_API_KEY")
)

MODEL_NAME = "meta/llama-3.1-405b-instruct"

def analyze_sentiment(transcript, product_name):
    """
    Analyzes the sentiment of a product review transcript using an LLM.
    """
    prompt = f"""
    You are an expert sentiment analyst. Analyze the following transcript of a YouTube review for the product: "{product_name}".
    
    Transcript:
    "{transcript[:15000]}"  # Truncate to avoid token limits if necessary
    
    Task:
    1. Determine the overall sentiment (Positive, Negative, or Neutral).
    2. Extract key pros and cons mentioned.
    3. Provide a brief summary of the reviewer's opinion.
    4. Give a sentiment score from 0 (Extremely Negative) to 10 (Extremely Positive).

    Return the result in valid JSON format ONLY, with the following structure:
    {{
        "sentiment": "Positive/Negative/Neutral",
        "score": 8.5,
        "pros": ["pro1", "pro2"],
        "cons": ["con1", "con2"],
        "summary": "Brief summary here."
    }}
    """

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            top_p=0.7,
            max_tokens=1024,
            stream=False
        )
        
        response_content = completion.choices[0].message.content.strip()
        
        # Clean up potential markdown code blocks or extra text
        # Find the first '{' and last '}'
        start_idx = response_content.find('{')
        end_idx = response_content.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_content[start_idx:end_idx+1]
            return json.loads(json_str)
        else:
            logging.error(f"No JSON object found in response: {response_content[:100]}...")
            return None
        
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from LLM response: {e}")
        logging.error(f"Raw response content: {response_content}")
        return None
    except Exception as e:
        logging.error(f"Error analyzing sentiment: {e}")
        return None

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data", "transcripts")
    sentiment_dir = os.path.join(os.path.dirname(__file__), "sentiment_data")
    os.makedirs(sentiment_dir, exist_ok=True)
    
    if not os.path.exists(data_dir):
        logging.error(f"Transcripts directory not found: {data_dir}")
        return

    # Find all json files recursively
    json_files = glob.glob(os.path.join(data_dir, "**", "*.json"), recursive=True)
    
    if not json_files:
        logging.error("No transcript files found.")
        return

    for file_path in json_files:
        # Determine relative path to mirror structure
        rel_path = os.path.relpath(file_path, data_dir)
        
        # Determine output path
        output_path = os.path.join(sentiment_dir, rel_path)
        output_dir_for_file = os.path.dirname(output_path)
        os.makedirs(output_dir_for_file, exist_ok=True)
        
        # Extract product name
        parts = rel_path.split(os.sep)
        if len(parts) >= 2:
            product_name = parts[-2].replace('_', ' ')
        else:
            filename = os.path.basename(file_path)
            product_name = filename.replace('_transcripts.json', '').replace('.json', '').replace('_', ' ')

        logging.info(f"Processing {product_name} from {rel_path}...")
        
        # Load transcripts
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                transcripts_data = json.load(f)
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            continue
            
        # Load existing sentiment data if available
        sentiment_data = []
        existing_ids = set()
        
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    sentiment_data = json.load(f)
                    existing_ids = {item['video_id'] for item in sentiment_data}
                logging.info(f"Resuming {product_name}: Found {len(sentiment_data)} existing analyses.")
            except json.JSONDecodeError:
                logging.warning(f"Could not decode existing file {output_path}. Starting fresh.")

        count = 0
        total_to_process = len(transcripts_data)
        
        for item in transcripts_data:
            video_id = item.get('video_id')
            
            if video_id in existing_ids:
                continue
                
            transcript = item.get('transcript')
            if not transcript:
                continue
                
            logging.info(f"Analyzing sentiment for video: {video_id} ({len(existing_ids) + 1}/{total_to_process})")
            
            analysis = analyze_sentiment(transcript, product_name)
            
            if analysis:
                result_entry = {
                    "product": product_name,
                    "video_id": video_id,
                    "title": item.get('title'),
                    "url": item.get('url'),
                    "date": item.get('date'),
                    "sentiment_analysis": analysis
                }
                
                sentiment_data.append(result_entry)
                existing_ids.add(video_id)
                count += 1
                
                # Incremental save
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(sentiment_data, f, indent=4, ensure_ascii=False)
                except Exception as e:
                    logging.error(f"Failed to save progress: {e}")
            else:
                logging.warning(f"Skipping video {video_id} due to analysis failure.")
        
        logging.info(f"Finished {product_name} ({rel_path}). Total analyzed: {len(sentiment_data)}\n")

if __name__ == "__main__":
    main()
