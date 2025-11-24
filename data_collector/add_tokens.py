import json
import os
import glob
from pathlib import Path
import tiktoken

def count_tokens(text, encoding_name="cl100k_base"):
    """
    Count the number of tokens in a text string using tiktoken.
    """
    if not text or not isinstance(text, str):
        return 0
    
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        print(f"Error counting tokens: {e}")
        return 0

def process_file(file_path):
    print(f"Processing {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updated_count = 0
        total_tokens = 0
        
        for entry in data:
            transcript = entry.get('transcript', '')
            token_count = count_tokens(transcript)
            
            # Update if missing or different (though usually we just overwrite)
            entry['token_count'] = token_count
            total_tokens += token_count
            updated_count += 1
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return len(data), total_tokens
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, 0

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data", "transcripts")
    if not os.path.exists(data_dir):
        print(f"Transcripts directory not found: {data_dir}")
        return

    # Find all json files recursively
    json_files = glob.glob(os.path.join(data_dir, "**", "*.json"), recursive=True)
    
    if not json_files:
        print("No transcript files found.")
        return

    print("=" * 90)
    print(f"{'File':<50} {'Videos':>10} {'Total Tokens':>15} {'Avg Tokens':>12}")
    print("-" * 90)

    grand_total_videos = 0
    grand_total_tokens = 0

    for file_path in json_files:
        # Determine display name
        rel_path = os.path.relpath(file_path, data_dir)
        
        video_count, tokens = process_file(file_path)
        
        avg_tokens = tokens // video_count if video_count > 0 else 0
        
        # Truncate path if too long
        display_name = rel_path if len(rel_path) < 48 else "..." + rel_path[-45:]
        
        print(f"{display_name:<50} {video_count:>10} {tokens:>15,} {avg_tokens:>12,}")
        
        grand_total_videos += video_count
        grand_total_tokens += tokens

    print("-" * 90)
    print(f"{'TOTAL':<50} {grand_total_videos:>10} {grand_total_tokens:>15,} {grand_total_tokens//grand_total_videos if grand_total_videos else 0:>12,}")
    print("=" * 90)

if __name__ == "__main__":
    main()
