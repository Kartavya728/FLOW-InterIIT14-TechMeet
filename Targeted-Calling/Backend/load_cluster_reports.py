"""
Load cluster reports from report_gen/output_reports into the database.
"""
import os
import json
import sqlite3
from datetime import datetime
from database import get_db_connection, init_db, seed_categories

# Paths
BACKEND_DIR = os.path.dirname(__file__)
REPORTS_DIR = os.path.join(os.path.dirname(BACKEND_DIR), 'report_gen', 'output_reports')


def clear_existing_data():
    """Clear existing data from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM users')
    cursor.execute('DELETE FROM cluster_insights')
    cursor.execute('DELETE FROM reports')
    
    conn.commit()
    conn.close()
    print("✅ Cleared existing data")


def load_cluster_reports():
    """Load cluster reports from output_reports folder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all JSON files (not IDS files)
    json_files = [f for f in os.listdir(REPORTS_DIR) 
                  if f.endswith('.json') and '_IDS' not in f]
    
    print(f"\n📂 Found {len(json_files)} cluster reports\n")
    
    for json_file in json_files:
        # Parse filename: CLUSTER_X_YYYYMMDD_HHMMSS.json
        parts = json_file.replace('.json', '').split('_')
        cluster_id = int(parts[1])
        timestamp_str = f"{parts[2]}_{parts[3]}"
        
        # Load main report JSON
        report_path = os.path.join(REPORTS_DIR, json_file)
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # Load customer IDs
        ids_file = json_file.replace('.json', '_IDS.json')
        ids_path = os.path.join(REPORTS_DIR, ids_file)
        with open(ids_path, 'r') as f:
            ids_data = json.load(f)
        
        customer_ids = ids_data.get('customer_ids', [])
        customer_count = len(set(customer_ids))  # Remove duplicates
        
        # Create batch_id from cluster info
        batch_id = f"CLUSTER_{cluster_id}_{timestamp_str}"
        
        # Format timestamp for display
        dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        timestamp_iso = dt.isoformat()
        
        # PDF filename
        pdf_file = json_file.replace('.json', '.pdf')
        
        # Generate unique report ID
        report_id = f"RPT_{batch_id}"
        
        # Insert report
        cursor.execute('''
            INSERT OR REPLACE INTO reports (
                id, batch_id, category_id, cluster_id, timestamp,
                total_calls, successful_calls, report_file,
                cluster_summary, avg_confidence,
                confidence_min, confidence_max, confidence_median,
                admin_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id,
            batch_id,
            'carLoans',  # Map to car loans only
            cluster_id,
            timestamp_iso,
            customer_count,
            customer_count,  # Assume all successful for now
            pdf_file,
            report_data.get('cluster_summary', ''),
            report_data.get('avg_confidence', 0.0),
            report_data.get('confidence_distribution', {}).get('min', 0.0),
            report_data.get('confidence_distribution', {}).get('max', 0.0),
            report_data.get('confidence_distribution', {}).get('median', 0.0),
            report_data.get('admin_summary', '')
        ))
        
        # Insert customer IDs
        unique_customers = list(set(customer_ids))
        for idx, customer_id in enumerate(unique_customers):
            user_id = f"USR_{report_id}_{idx}"
            cursor.execute('''
                INSERT OR REPLACE INTO users (id, user_id, report_id)
                VALUES (?, ?, ?)
            ''', (user_id, customer_id, report_id))
        
        # Insert insights
        # Prediction factors
        for factor in report_data.get('prediction_factors', []):
            cursor.execute('''
                INSERT INTO cluster_insights (report_id, insight_type, insight_text)
                VALUES (?, ?, ?)
            ''', (report_id, 'prediction_factor', factor))
        
        # Customer behavior patterns
        for pattern in report_data.get('customer_behavior_patterns', []):
            cursor.execute('''
                INSERT INTO cluster_insights (report_id, insight_type, insight_text)
                VALUES (?, ?, ?)
            ''', (report_id, 'behavior_pattern', pattern))
        
        # Exemplar insights
        for insight in report_data.get('exemplar_insights', []):
            cursor.execute('''
                INSERT INTO cluster_insights (report_id, insight_type, insight_text)
                VALUES (?, ?, ?)
            ''', (report_id, 'exemplar_insight', insight))
        
        # Recommendations
        for recommendation in report_data.get('recommendations', []):
            cursor.execute('''
                INSERT INTO cluster_insights (report_id, insight_type, insight_text)
                VALUES (?, ?, ?)
            ''', (report_id, 'recommendation', recommendation))
        
        print(f"✅ Loaded: {batch_id} - Cluster {cluster_id} ({customer_count} customers)")
    
    conn.commit()
    conn.close()
    print(f"\n🎉 Successfully loaded {len(json_files)} cluster reports!")


if __name__ == '__main__':
    print("🔄 Initializing database...")
    init_db()
    seed_categories()
    
    print("\n🗑️  Clearing existing data...")
    clear_existing_data()
    
    print("\n📥 Loading cluster reports from output_reports folder...")
    load_cluster_reports()
    
    print("\n✅ Data loading complete!")
