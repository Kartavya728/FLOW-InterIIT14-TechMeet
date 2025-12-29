"""
Sync cluster reports from report_gen/output_reports folder to database.
This module provides functions to keep the database in sync with the file system.
"""
import os
import json
from datetime import datetime
from database import get_db_connection, init_db, seed_categories

# Paths
BACKEND_DIR = os.path.dirname(__file__)
REPORTS_DIR = os.path.join(os.path.dirname(BACKEND_DIR), 'report_gen', 'output_reports')


def sync_cluster_reports():
    """
    Sync cluster reports from output_reports folder to database.
    - Adds new reports found in files
    - Updates existing reports if files changed
    - Removes reports from DB if files deleted
    Returns dict with sync statistics.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {
        'added': 0,
        'updated': 0,
        'deleted': 0,
        'unchanged': 0,
        'total_files': 0,
        'total_db': 0
    }
    
    try:
        # Get all JSON files (not IDS files) from folder
        if not os.path.exists(REPORTS_DIR):
            print(f"⚠️ Output reports directory not found: {REPORTS_DIR}")
            return stats
            
        json_files = [f for f in os.listdir(REPORTS_DIR) 
                      if f.endswith('.json') and '_IDS' not in f]
        
        stats['total_files'] = len(json_files)
        print(f"\n📂 Found {len(json_files)} cluster report files")
        
        # Get existing reports from database
        existing_reports = {}
        db_reports = cursor.execute('SELECT id, batch_id FROM reports').fetchall()
        for row in db_reports:
            existing_reports[row[1]] = row[0]  # batch_id -> report_id
        
        stats['total_db'] = len(existing_reports)
        print(f"💾 Found {len(existing_reports)} reports in database")
        
        # Track which batch_ids we've seen in files
        file_batch_ids = set()
        
        # Process each file
        for json_file in json_files:
            try:
                # Parse filename: CLUSTER_X_YYYYMMDD_HHMMSS.json
                parts = json_file.replace('.json', '').split('_')
                if len(parts) < 4:
                    print(f"⚠️ Skipping invalid filename: {json_file}")
                    continue
                    
                cluster_id = int(parts[1])
                timestamp_str = f"{parts[2]}_{parts[3]}"
                batch_id = f"CLUSTER_{cluster_id}_{timestamp_str}"
                file_batch_ids.add(batch_id)
                
                # Load main report JSON
                report_path = os.path.join(REPORTS_DIR, json_file)
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                
                # Load customer IDs
                ids_file = json_file.replace('.json', '_IDS.json')
                ids_path = os.path.join(REPORTS_DIR, ids_file)
                
                if not os.path.exists(ids_path):
                    print(f"⚠️ Missing IDS file for {json_file}, skipping")
                    continue
                    
                with open(ids_path, 'r') as f:
                    ids_data = json.load(f)
                
                customer_ids = ids_data.get('customer_ids', [])
                customer_count = len(set(customer_ids))  # Remove duplicates
                
                # Format timestamp
                dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                timestamp_iso = dt.isoformat()
                
                # PDF filename
                pdf_file = json_file.replace('.json', '.pdf')
                
                # Generate report ID
                report_id = f"RPT_{batch_id}"
                
                # Check if report exists
                if batch_id in existing_reports:
                    # Report exists - update it
                    cursor.execute('''
                        UPDATE reports SET
                            cluster_summary = ?,
                            avg_confidence = ?,
                            confidence_min = ?,
                            confidence_max = ?,
                            confidence_median = ?,
                            admin_summary = ?,
                            total_calls = ?,
                            successful_calls = ?
                        WHERE id = ?
                    ''', (
                        report_data.get('cluster_summary', ''),
                        report_data.get('avg_confidence', 0.0),
                        report_data.get('confidence_distribution', {}).get('min', 0.0),
                        report_data.get('confidence_distribution', {}).get('max', 0.0),
                        report_data.get('confidence_distribution', {}).get('median', 0.0),
                        report_data.get('admin_summary', ''),
                        customer_count,
                        customer_count,
                        report_id
                    ))
                    stats['updated'] += 1
                    print(f"🔄 Updated: {batch_id}")
                else:
                    # New report - insert it
                    cursor.execute('''
                        INSERT INTO reports (
                            id, batch_id, category_id, cluster_id, timestamp,
                            total_calls, successful_calls, report_file,
                            cluster_summary, avg_confidence,
                            confidence_min, confidence_max, confidence_median,
                            admin_summary
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        report_id,
                        batch_id,
                        'carLoans',
                        cluster_id,
                        timestamp_iso,
                        customer_count,
                        customer_count,
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
                            INSERT INTO users (id, user_id, report_id)
                            VALUES (?, ?, ?)
                        ''', (user_id, customer_id, report_id))
                    
                    # Insert insights
                    for factor in report_data.get('prediction_factors', []):
                        cursor.execute('''
                            INSERT INTO cluster_insights (report_id, insight_type, insight_text)
                            VALUES (?, ?, ?)
                        ''', (report_id, 'prediction_factor', factor))
                    
                    for pattern in report_data.get('customer_behavior_patterns', []):
                        cursor.execute('''
                            INSERT INTO cluster_insights (report_id, insight_type, insight_text)
                            VALUES (?, ?, ?)
                        ''', (report_id, 'behavior_pattern', pattern))
                    
                    for insight in report_data.get('exemplar_insights', []):
                        cursor.execute('''
                            INSERT INTO cluster_insights (report_id, insight_type, insight_text)
                            VALUES (?, ?, ?)
                        ''', (report_id, 'exemplar_insight', insight))
                    
                    for recommendation in report_data.get('recommendations', []):
                        cursor.execute('''
                            INSERT INTO cluster_insights (report_id, insight_type, insight_text)
                            VALUES (?, ?, ?)
                        ''', (report_id, 'recommendation', recommendation))
                    
                    stats['added'] += 1
                    print(f"✅ Added: {batch_id} ({customer_count} customers)")
                    
            except Exception as e:
                print(f"❌ Error processing {json_file}: {e}")
                continue
        
        # Remove reports from DB that no longer have files
        for batch_id, report_id in existing_reports.items():
            if batch_id not in file_batch_ids:
                cursor.execute('DELETE FROM cluster_insights WHERE report_id = ?', (report_id,))
                cursor.execute('DELETE FROM users WHERE report_id = ?', (report_id,))
                cursor.execute('DELETE FROM reports WHERE id = ?', (report_id,))
                stats['deleted'] += 1
                print(f"🗑️ Deleted: {batch_id} (file no longer exists)")
        
        stats['unchanged'] = stats['total_files'] - stats['added'] - stats['updated']
        
        conn.commit()
        
        print(f"\n📊 Sync Summary:")
        print(f"   ✅ Added: {stats['added']}")
        print(f"   🔄 Updated: {stats['updated']}")
        print(f"   🗑️ Deleted: {stats['deleted']}")
        print(f"   ⏭️ Unchanged: {stats['unchanged']}")
        print(f"   📁 Total in files: {stats['total_files']}")
        print(f"   💾 Total in DB: {stats['total_db']}")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    return stats


if __name__ == '__main__':
    print("🔄 Ensuring database is initialized...")
    init_db()
    seed_categories()
    
    print("\n📥 Syncing cluster reports from output_reports folder...")
    stats = sync_cluster_reports()
    
    print("\n✅ Sync complete!")
