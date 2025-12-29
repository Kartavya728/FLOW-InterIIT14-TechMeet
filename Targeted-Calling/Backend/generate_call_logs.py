"""
AI Call Log Generator
Processes call transcripts from carLoanPredictor/call_transcripts.json
and generates detailed call analytics using OpenAI LLM.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TRANSCRIPTS_FILE = PROJECT_ROOT / "carLoanPredictor" / "call_transcripts.json"
CALL_LOGS_DIR = Path(__file__).parent / "mock call logs"
TRANSCRIPTS_DIR = Path(__file__).parent / "mock transcripts"

# Create directories
os.makedirs(CALL_LOGS_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

# OpenAI setup (using same key as llm_gen.py)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found")

client = OpenAI(api_key=OPENAI_API_KEY)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Track processed calls
PROCESSED_CALLS_FILE = Path(__file__).parent / "processed_calls.json"

def load_processed_calls():
    """Load list of already processed call IDs"""
    if PROCESSED_CALLS_FILE.exists():
        with open(PROCESSED_CALLS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_calls(processed_set):
    """Save list of processed call IDs"""
    with open(PROCESSED_CALLS_FILE, 'w') as f:
        json.dump(list(processed_set), f)

def analyze_call_with_llm(customer_id, transcript, timestamp):
    """Use OpenAI to analyze call transcript and extract insights"""
    
    prompt = f"""Analyze this customer call transcript for a car loan product and extract detailed information.

Call Details:
- Customer ID: {customer_id}
- Timestamp: {timestamp}

Transcript:
{transcript}

Provide analysis in EXACTLY this JSON format (respond ONLY with valid JSON, no other text):

{{
  "customer_name": "Generate a realistic Indian name based on the customer ID",
  "product_type": "car loan",
  "call_duration": <estimated duration in seconds between 60-300>,
  "user_response": "<HIGH|MEDIUM|LOW based on customer interest level>",
  "willingness_score": <score from 0-100 based on customer's willingness to proceed>,
  "main_points": [
    "Key point 1 discussed in the conversation",
    "Key point 2 discussed",
    "Key point 3 discussed"
  ],
  "customer_doubts": [
    "Doubt or concern 1 raised by customer",
    "Doubt or concern 2 (if any)"
  ],
  "agent_notes": "Brief summary of agent's observations about the customer",
  "call_outcome": "<INTERESTED|NOT_INTERESTED|NEEDS_FOLLOWUP|CALLBACK_REQUESTED>",
  "next_action": "Recommended next step for this customer"
}}

Analyze the actual conversation and be realistic. If the customer shows no interest, reflect that honestly."""

    try:
        print(f"🔵 Analyzing call for {customer_id} with OpenAI...")
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI call analytics expert. Respond ONLY with valid JSON. No markdown, no code blocks, just pure JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=1000
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Clean up response
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
        
        # Parse JSON
        analysis = json.loads(raw)
        print(f"✅ Analysis completed for {customer_id}")
        
        return analysis
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed for {customer_id}: {e}")
        print(f"Raw response: {raw[:200]}")
        # Return default structure
        return create_default_analysis(customer_id)
        
    except Exception as e:
        print(f"❌ OpenAI API failed for {customer_id}: {e}")
        return create_default_analysis(customer_id)

def create_default_analysis(customer_id):
    """Create a default analysis if LLM fails"""
    return {
        "customer_name": f"Customer {customer_id[-4:]}",
        "product_type": "car loan",
        "call_duration": 120,
        "user_response": "LOW",
        "willingness_score": 30,
        "main_points": [
            "Discussed car loan options",
            "Mentioned interest rates",
            "Explained documentation process"
        ],
        "customer_doubts": [
            "Concerns about eligibility",
            "Questions about processing time"
        ],
        "agent_notes": "Customer showed limited interest. Needs more information.",
        "call_outcome": "NEEDS_FOLLOWUP",
        "next_action": "Send detailed information via email and follow up in 3 days"
    }

def generate_call_log(customer_id, transcript_data):
    """Generate complete call log JSON file"""
    
    customer_id = transcript_data["customer_id"]
    transcript = transcript_data["transcript"]
    timestamp = transcript_data["timestamp"]
    
    # Analyze with LLM
    analysis = analyze_call_with_llm(customer_id, transcript, timestamp)
    
    # Generate call ID
    call_id = f"CALL_{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create transcript file
    transcript_filename = f"{call_id}_transcript.txt"
    transcript_path = TRANSCRIPTS_DIR / transcript_filename
    with open(transcript_path, 'w') as f:
        f.write(transcript)
    
    # Create complete call log
    call_log = {
        "call_id": call_id,
        "customer_id": customer_id,
        "customer_name": analysis["customer_name"],
        "product_type": analysis["product_type"],
        "timestamp": timestamp,
        "call_duration": analysis["call_duration"],
        "user_response": analysis["user_response"],
        "willingness_score": analysis["willingness_score"],
        "main_points": analysis["main_points"],
        "customer_doubts": analysis["customer_doubts"],
        "agent_notes": analysis["agent_notes"],
        "call_outcome": analysis["call_outcome"],
        "next_action": analysis["next_action"],
        "transcript_file": transcript_filename
    }
    
    # Save call log
    call_log_path = CALL_LOGS_DIR / f"{call_id}.json"
    with open(call_log_path, 'w') as f:
        json.dump(call_log, f, indent=2)
    
    print(f"✅ Generated call log: {call_log_path}")
    return call_log

def process_new_transcripts():
    """Process any new transcripts from call_transcripts.json"""
    
    if not TRANSCRIPTS_FILE.exists():
        print(f"⚠️ Transcripts file not found: {TRANSCRIPTS_FILE}")
        return []
    
    # Load transcripts
    try:
        with open(TRANSCRIPTS_FILE, 'r') as f:
            transcripts = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load transcripts: {e}")
        return []
    
    # Load processed calls
    processed = load_processed_calls()
    
    # Process new calls
    new_logs = []
    for customer_id, transcript_data in transcripts.items():
        if customer_id not in processed:
            print(f"\n📞 Processing new call for {customer_id}...")
            try:
                call_log = generate_call_log(customer_id, transcript_data)
                new_logs.append(call_log)
                processed.add(customer_id)
                print(f"✅ Processed {customer_id}")
            except Exception as e:
                print(f"❌ Failed to process {customer_id}: {e}")
    
    # Save updated processed list
    save_processed_calls(processed)
    
    if new_logs:
        print(f"\n✅ Processed {len(new_logs)} new call(s)")
    else:
        print(f"\n⏭️ No new calls to process")
    
    return new_logs

def continuous_processing(interval=5):
    """Continuously monitor and process new transcripts"""
    print(f"🚀 Starting continuous call log processing...")
    print(f"📂 Monitoring: {TRANSCRIPTS_FILE}")
    print(f"⏱️ Check interval: {interval} seconds")
    print(f"📁 Output: {CALL_LOGS_DIR}")
    print("-" * 60)
    
    while True:
        try:
            new_logs = process_new_transcripts()
            if new_logs:
                print(f"✨ Generated {len(new_logs)} new call log(s)")
        except KeyboardInterrupt:
            print("\n🛑 Stopping call log processor...")
            break
        except Exception as e:
            print(f"❌ Error in processing loop: {e}")
        
        time.sleep(interval)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # Run in continuous mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        continuous_processing(interval)
    else:
        # Run once
        print("🚀 Processing call transcripts (one-time run)...")
        new_logs = process_new_transcripts()
        print(f"\n✅ Complete! Processed {len(new_logs)} call(s)")
        print("\nTo run continuously, use: python generate_call_logs.py --continuous [interval_seconds]")
