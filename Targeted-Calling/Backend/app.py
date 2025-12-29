"""
Flask API server for the Targeted Calling application with WebSocket support.
"""
import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from database import get_db_connection, init_db, seed_categories

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Paths
BACKEND_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
MOCK_AUDIO_DIR = os.path.join(BACKEND_DIR, 'mock audio')
MOCK_REPORTS_DIR = os.path.join(BACKEND_DIR, 'mock reports')
MOCK_CALL_LOGS_DIR = os.path.join(BACKEND_DIR, 'mock call logs')
MOCK_TRANSCRIPTS_DIR = os.path.join(BACKEND_DIR, 'mock transcripts')
OUTPUT_REPORTS_DIR = os.path.join(PROJECT_DIR, 'report_gen', 'output_reports')

# Initialize database on startup
init_db()
seed_categories()


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('✅ Client connected')
    emit('connected', {'message': 'Connected to real-time updates'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('❌ Client disconnected')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'API is running'})


# Notification endpoint for NATS consumer
@app.route('/api/notify-update', methods=['POST'])
def notify_update():
    """Receive update notifications from NATS consumer and broadcast via WebSocket"""
    data = request.json
    
    # Broadcast to all connected clients (Flask-SocketIO 5.x compatible)
    socketio.emit('customer_update', data, namespace='/')
    
    return jsonify({'status': 'notified'})


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories."""
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    
    return jsonify([dict(cat) for cat in categories])


@app.route('/api/sync-reports', methods=['POST'])
def sync_reports_endpoint():
    """Manually trigger sync of reports from filesystem."""
    try:
        from sync_cluster_reports import sync_cluster_reports
        stats = sync_cluster_reports()
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f"Synced successfully: {stats['added']} added, {stats['updated']} updated, {stats['deleted']} deleted"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reports', methods=['GET'])
def get_reports():
    """Get reports, optionally filtered by category."""
    category = request.args.get('category')
    
    # Sync reports from filesystem before fetching
    try:
        from sync_cluster_reports import sync_cluster_reports
        sync_cluster_reports()
    except Exception as e:
        print(f"Warning: Could not sync reports: {e}")
    
    conn = get_db_connection()
    
    if category:
        reports = conn.execute('''
            SELECT r.*, c.label as category_label, c.prefix as category_prefix
            FROM reports r
            JOIN categories c ON r.category_id = c.id
            WHERE r.category_id = ?
            ORDER BY r.timestamp DESC
        ''', (category,)).fetchall()
    else:
        reports = conn.execute('''
            SELECT r.*, c.label as category_label, c.prefix as category_prefix
            FROM reports r
            JOIN categories c ON r.category_id = c.id
            ORDER BY r.timestamp DESC
        ''').fetchall()
    
    conn.close()
    
    # Get user IDs for each report
    result = []
    for report in reports:
        report_dict = dict(report)
        conn = get_db_connection()
        users = conn.execute('''
            SELECT user_id FROM users WHERE report_id = ?
        ''', (report_dict['id'],)).fetchall()
        conn.close()
        report_dict['userIds'] = [u['user_id'] for u in users]
        result.append(report_dict)
    
    return jsonify(result)


@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    """Get a single report with all details."""
    conn = get_db_connection()
    
    report = conn.execute('''
        SELECT r.*, c.label as category_label, c.prefix as category_prefix
        FROM reports r
        JOIN categories c ON r.category_id = c.id
        WHERE r.id = ?
    ''', (report_id,)).fetchone()
    
    if not report:
        conn.close()
        return jsonify({'error': 'Report not found'}), 404
    
    users = conn.execute('''
        SELECT * FROM users WHERE report_id = ?
    ''', (report_id,)).fetchall()
    
    # Get cluster insights
    insights = conn.execute('''
        SELECT * FROM cluster_insights WHERE report_id = ?
    ''', (report_id,)).fetchall()
    
    conn.close()
    
    report_dict = dict(report)
    report_dict['users'] = [dict(user) for user in users]
    report_dict['userIds'] = [u['user_id'] for u in users]
    
    # Group insights by type
    report_dict['insights'] = {
        'prediction_factors': [dict(i)['insight_text'] for i in insights if dict(i)['insight_type'] == 'prediction_factor'],
        'behavior_patterns': [dict(i)['insight_text'] for i in insights if dict(i)['insight_type'] == 'behavior_pattern'],
        'exemplar_insights': [dict(i)['insight_text'] for i in insights if dict(i)['insight_type'] == 'exemplar_insight'],
        'recommendations': [dict(i)['insight_text'] for i in insights if dict(i)['insight_type'] == 'recommendation']
    }
    
    return jsonify(report_dict)


@app.route('/api/reports/<report_id>/users', methods=['GET'])
def get_report_users(report_id):
    """Get all users for a specific report."""
    conn = get_db_connection()
    
    users = conn.execute('''
        SELECT * FROM users WHERE report_id = ?
    ''', (report_id,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(user) for user in users])


@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get a single user by user_id."""
    conn = get_db_connection()
    
    user = conn.execute('''
        SELECT * FROM users WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(dict(user))


# Serve static files (audio and reports)
@app.route('/api/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    """Serve audio files."""
    return send_from_directory(MOCK_AUDIO_DIR, filename)


@app.route('/api/reports/file/<filename>', methods=['GET'])
def serve_report_file(filename):
    """Serve PDF report files from output_reports folder."""
    return send_from_directory(OUTPUT_REPORTS_DIR, filename)


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics."""
    conn = get_db_connection()
    
    stats = {
        'totalReports': conn.execute('SELECT COUNT(*) FROM reports').fetchone()[0],
        'totalUsers': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'totalAgreed': conn.execute('SELECT COUNT(*) FROM users WHERE agreed = 1').fetchone()[0],
        'totalDeclined': conn.execute('SELECT COUNT(*) FROM users WHERE agreed = 0').fetchone()[0],
    }
    
    # Category-wise stats
    category_stats = conn.execute('''
        SELECT c.id, c.label, 
               COUNT(DISTINCT r.id) as report_count,
               SUM(r.total_calls) as total_calls,
               SUM(r.successful_calls) as successful_calls
        FROM categories c
        LEFT JOIN reports r ON c.id = r.category_id
        GROUP BY c.id
    ''').fetchall()
    
    conn.close()
    
    stats['categoryStats'] = [dict(cs) for cs in category_stats]
    
    return jsonify(stats)


# AI Call Logs endpoints
CALL_TRANSCRIPTS_FILE = os.path.join(PROJECT_DIR, 'carLoanPredictor', 'call_transcripts.json')
CALL_LOGS_CACHE_FILE = os.path.join(MOCK_CALL_LOGS_DIR, '_cache.json')

def load_call_logs_cache():
    """Load cached AI-processed call logs"""
    if os.path.exists(CALL_LOGS_CACHE_FILE):
        try:
            with open(CALL_LOGS_CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_call_logs_cache(cache):
    """Save AI-processed call logs cache"""
    try:
        with open(CALL_LOGS_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Failed to save cache: {e}")

def analyze_call_with_ai(customer_id, transcript, timestamp):
    """Analyze call using OpenAI (same as generate_call_logs.py)"""
    from openai import OpenAI
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""Analyze this customer call transcript for a car loan product and extract detailed information.

Call Details:
- Customer ID: {customer_id}
- Timestamp: {timestamp}

Transcript:
{transcript}

Provide analysis in EXACTLY this JSON format (respond ONLY with valid JSON):

{{
  "customer_name": "Generate a realistic Indian name",
  "product_type": "car loan",
  "call_duration": <estimated seconds 60-300>,
  "user_response": "<HIGH|MEDIUM|LOW>",
  "willingness_score": <0-100>,
  "main_points": ["Point 1", "Point 2", "Point 3"],
  "customer_doubts": ["Doubt 1", "Doubt 2"],
  "agent_notes": "Brief observations",
  "call_outcome": "<INTERESTED|NOT_INTERESTED|NEEDS_FOLLOWUP|CALLBACK_REQUESTED>",
  "next_action": "Recommended next step"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI call analytics expert. Respond ONLY with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
        
        return json.loads(raw)
    except Exception as e:
        print(f"AI analysis failed for {customer_id}: {e}")
        # Return default
        return {
            "customer_name": f"Customer {customer_id[-4:]}",
            "product_type": "car loan",
            "call_duration": 120,
            "user_response": "LOW",
            "willingness_score": 30,
            "main_points": ["Discussed car loan options", "Mentioned interest rates", "Explained documentation"],
            "customer_doubts": ["Concerns about eligibility"],
            "agent_notes": "Customer showed limited interest",
            "call_outcome": "NEEDS_FOLLOWUP",
            "next_action": "Follow up in 3 days"
        }

@app.route('/api/call-logs', methods=['GET'])
def get_call_logs():
    """Get all AI call logs from call_transcripts.json, optionally filtered by product type."""
    product_type = request.args.get('product_type')
    
    # Check if call_transcripts.json exists
    if not os.path.exists(CALL_TRANSCRIPTS_FILE):
        return jsonify([])
    
    try:
        # Load transcripts
        with open(CALL_TRANSCRIPTS_FILE, 'r') as f:
            transcripts = json.load(f)
        
        # Load cache
        cache = load_call_logs_cache()
        updated_cache = False
        
        call_logs = []
        
        for customer_id, data in transcripts.items():
            # Check if already in cache
            if customer_id in cache:
                call_log = cache[customer_id]
            else:
                print(f"Processing new call for {customer_id}...")
                # Analyze with AI
                analysis = analyze_call_with_ai(
                    customer_id,
                    data.get('transcript', ''),
                    data.get('timestamp', '')
                )
                
                # Generate call ID
                call_id = f"CALL_{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Create call log
                call_log = {
                    "call_id": call_id,
                    "customer_id": customer_id,
                    "customer_name": analysis["customer_name"],
                    "product_type": analysis["product_type"],
                    "timestamp": data.get('timestamp', datetime.now().isoformat()),
                    "call_duration": analysis["call_duration"],
                    "user_response": analysis["user_response"],
                    "willingness_score": analysis["willingness_score"],
                    "main_points": analysis["main_points"],
                    "customer_doubts": analysis["customer_doubts"],
                    "agent_notes": analysis["agent_notes"],
                    "call_outcome": analysis["call_outcome"],
                    "next_action": analysis["next_action"],
                    "transcript_file": f"{call_id}_transcript.txt"
                }
                
                # Save transcript file
                transcript_path = os.path.join(MOCK_TRANSCRIPTS_DIR, call_log["transcript_file"])
                with open(transcript_path, 'w') as f:
                    f.write(data.get('transcript', ''))
                
                # Add to cache
                cache[customer_id] = call_log
                updated_cache = True
                print(f"✅ Processed {customer_id}")
            
            # Apply product filter if specified
            if product_type:
                if call_log.get('product_type') == product_type:
                    call_logs.append(call_log)
            else:
                call_logs.append(call_log)
        
        # Save updated cache
        if updated_cache:
            save_call_logs_cache(cache)
        
        # Sort by timestamp (most recent first)
        call_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify(call_logs)
        
    except Exception as e:
        print(f"Error reading call transcripts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])


@app.route('/api/call-logs/<call_id>', methods=['GET'])
def get_call_log(call_id):
    """Get a specific call log by ID."""
    import json
    import glob
    
    log_files = glob.glob(os.path.join(MOCK_CALL_LOGS_DIR, '*.json'))
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)
                if log_data.get('call_id') == call_id:
                    return jsonify(log_data)
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
    
    return jsonify({'error': 'Call log not found'}), 404


@app.route('/api/transcripts/<transcript_file>', methods=['GET'])
def get_transcript(transcript_file):
    """Get a transcript file content."""
    try:
        transcript_path = os.path.join(MOCK_TRANSCRIPTS_DIR, transcript_file)
        with open(transcript_path, 'r') as f:
            content = f.read()
        return jsonify({'content': content})
    except FileNotFoundError:
        return jsonify({'error': 'Transcript not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/call-logs/stats', methods=['GET'])
def get_call_logs_stats():
    """Get statistics for AI call logs."""
    import json
    import glob
    
    log_files = glob.glob(os.path.join(MOCK_CALL_LOGS_DIR, '*.json'))
    
    total_calls = len(log_files)
    high_interest = 0
    medium_interest = 0
    low_interest = 0
    
    product_stats = {
        'car loan': 0,
        'mutual funds': 0,
        'nifty': 0,
        'others': 0
    }
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)
                
                # Count by user response
                response = log_data.get('user_response', '').upper()
                if response == 'HIGH':
                    high_interest += 1
                elif response == 'MEDIUM':
                    medium_interest += 1
                elif response == 'LOW':
                    low_interest += 1
                
                # Count by product type
                product = log_data.get('product_type', '').lower()
                if product in product_stats:
                    product_stats[product] += 1
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
    
    return jsonify({
        'total_calls': total_calls,
        'high_interest': high_interest,
        'medium_interest': medium_interest,
        'low_interest': low_interest,
        'product_stats': product_stats
    })


# Individual Report Generation endpoint
@app.route('/api/generate-individual-report/<customer_id>', methods=['POST'])
def generate_individual_report(customer_id):
    """Generate individual customer report by calling gen_ind_report.py"""
    import subprocess
    import glob
    
    try:
        # Path to the report generation script
        gen_script = os.path.join(PROJECT_DIR, 'report_gen', 'gen_ind_report.py')
        
        if not os.path.exists(gen_script):
            return jsonify({'error': 'Report generation script not found'}), 404
        
        # Check if required data files exist
        masterfile_path = os.path.join(PROJECT_DIR, 'MASTERFILE.csv')
        prediction_cache_path = os.path.join(PROJECT_DIR, 'report_gen', 'prediction_cache.csv')
        
        if not os.path.exists(masterfile_path):
            return jsonify({
                'error': 'MASTERFILE.csv not found',
                'details': f'Required file MASTERFILE.csv not found at {masterfile_path}. Please ensure the data files are in place.'
            }), 404
        
        if not os.path.exists(prediction_cache_path):
            return jsonify({
                'error': 'prediction_cache.csv not found',
                'details': f'Required file prediction_cache.csv not found. Please run the prediction pipeline first.'
            }), 404
        
        print(f"Generating report for customer: {customer_id}")
        
        # Call the script
        result = subprocess.run(
            ['python', gen_script, customer_id],
            cwd=os.path.join(PROJECT_DIR, 'report_gen'),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr
            
            # Parse specific errors for better user feedback
            if 'MASTERFILE not found' in error_msg:
                return jsonify({
                    'error': 'MASTERFILE.csv not found',
                    'details': 'The customer master data file is missing. Please contact the administrator.'
                }), 404
            elif 'customer_id' in error_msg and 'not found' in error_msg:
                return jsonify({
                    'error': 'Customer not found',
                    'details': f'Customer {customer_id} not found in the database. Please verify the customer ID.'
                }), 404
            elif 'ModuleNotFoundError' in error_msg or 'ImportError' in error_msg:
                # Extract module name
                module_match = error_msg.split("No module named '")
                module_name = module_match[1].split("'")[0] if len(module_match) > 1 else 'unknown'
                return jsonify({
                    'error': 'Missing dependencies',
                    'details': f'Required Python package "{module_name}" is not installed. Please contact the administrator.'
                }), 500
            else:
                print(f"Error generating report: {error_msg}")
                return jsonify({
                    'error': 'Report generation failed',
                    'details': error_msg[:500]  # Limit error message length
                }), 500
        
        # Find the generated PDF file
        individual_reports_dir = os.path.join(PROJECT_DIR, 'report_gen', 'individual_reports')
        pdf_pattern = os.path.join(individual_reports_dir, f'{customer_id}_*.pdf')
        pdf_files = glob.glob(pdf_pattern)
        
        if not pdf_files:
            return jsonify({
                'error': 'Report generated but PDF file not found',
                'details': f'The report script completed but no PDF was found at {pdf_pattern}'
            }), 500
        
        # Get the most recent file
        latest_pdf = max(pdf_files, key=os.path.getctime)
        pdf_filename = os.path.basename(latest_pdf)
        
        print(f"Report generated successfully: {pdf_filename}")
        
        return jsonify({
            'success': True,
            'filename': pdf_filename,
            'customer_id': customer_id
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'error': 'Report generation timed out',
            'details': 'The report generation took longer than 2 minutes. Please try again or contact support.'
        }), 408
    except Exception as e:
        print(f"Exception generating report: {e}")
        return jsonify({
            'error': 'Unexpected error',
            'details': str(e)
        }), 500


# Serve individual customer reports
@app.route('/api/individual-reports/<filename>', methods=['GET'])
def serve_individual_report(filename):
    """Serve individual customer report PDFs."""
    individual_reports_dir = os.path.join(PROJECT_DIR, 'report_gen', 'individual_reports')
    return send_from_directory(individual_reports_dir, filename)



if __name__ == '__main__':
    print("Starting Flask server with WebSocket support...")
    print("API available at http://localhost:5000")
    print("WebSocket available for real-time updates")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
