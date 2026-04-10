#!/usr/bin/env python3
"""
Flask Server for LinkedIn Scraper Integration
Provides API endpoint to trigger the enhanced LinkedIn scraper
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import subprocess
import json
import os
import sys
from pathlib import Path
import threading
from datetime import datetime

# Add monk path for AI wrappers
sys.path.insert(0, '/Users/Subho/monk')

app = Flask(__name__)
CORS(app)

# Global variable to track scraper status
scraper_status = {
    'running': False,
    'last_run': None,
    'error': None,
    'progress': 0,
    'message': ''
}

def run_scraper_in_background():
    """Run the LinkedIn scraper in background thread"""
    global scraper_status

    try:
        scraper_status.update({
            'running': True,
            'last_run': datetime.now().isoformat(),
            'error': None,
            'progress': 0,
            'message': 'Starting scraper...'
        })

        # Change to the directory with the scraper
        os.chdir('/Users/Subho')

        # Run the enhanced scraper
        process = subprocess.run([
            'python3', 'linkedin_post_scraper_enhanced.py'
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout

        scraper_status.update({
            'running': False,
            'progress': 100,
            'message': 'Scraping completed successfully'
        })

    except subprocess.TimeoutExpired:
        scraper_status.update({
            'running': False,
            'error': 'Scraper timeout after 10 minutes',
            'message': 'Timeout - please try again'
        })

    except Exception as e:
        scraper_status.update({
            'running': False,
            'error': str(e),
            'message': f'Error: {str(e)}'
        })

    finally:
        scraper_status['last_run'] = datetime.now().isoformat()

@app.route('/api/refresh-linkedin-data', methods=['POST'])
def refresh_linkedin_data():
    """API endpoint to trigger LinkedIn data refresh"""
    if scraper_status['running']:
        return jsonify({
            'success': False,
            'message': 'Scraper is already running. Please wait for it to complete.',
            'status': scraper_status
        }), 409

    # Start scraper in background thread
    thread = threading.Thread(target=run_scraper_in_background)
    thread.daemon = True
    thread.start()

    # Wait a moment for status to update
    import time
    time.sleep(1)

    return jsonify({
        'success': True,
        'message': 'Scraper started in background',
        'status': scraper_status
    })

@app.route('/api/scraper-status', methods=['GET'])
def get_scraper_status():
    """Get current scraper status"""
    return jsonify({
        'status': scraper_status
    })

@app.route('/api/load-linkedin-data', methods=['GET'])
def load_linkedin_data():
    """Load existing LinkedIn data from JSON file"""
    try:
        # Look for the enhanced LinkedIn database file
        json_file = '/Users/Subho/linkedin_jagadeesh_posts_database.json'

        if not Path(json_file).exists():
            # Try to find any LinkedIn database file
            import glob
            linkedin_files = glob.glob('/Users/Subho/linkedin_*_database*.json')
            if linkedin_files:
                json_file = linkedin_files[0]
            else:
                return jsonify({
                    'success': False,
                    'message': 'No LinkedIn database found. Please run scraper first.',
                    'posts': []
                })

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return jsonify({
            'success': True,
            'posts': data.get('posts_by_category', {}).get('Business & Strategy', []) +
                     data.get('posts_by_category', {}).get('Career & Professional Development', []) +
                     data.get('posts_by_category', {}).get('Technology & AI', []),
            'categories': data.get('categories', {}),
            'total_posts': data.get('total_posts', 0)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading data: {str(e)}',
            'posts': []
        })

@app.route('/')
def serve_app():
    """Serve the main application"""
    # Serve the enhanced HTML file directly
    return send_file('/Users/Subho/simple_working_search.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return app.send_static_file(path)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'scraper_status': scraper_status,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting LinkedIn Scraper Server...")
    print("📍 Server: http://localhost:5001")
    print("🔄 Scraper API: /api/refresh-linkedin-data")
    print("📊 Status API: /api/scraper-status")
    print("📁 Load Data API: /api/load-linkedin-data")
    print("💚 Health Check: /api/health")
    print()

    # Try to load initial data
    try:
        load_linkedin_data()
        print("✅ Initial data loaded successfully")
    except:
        print("⚠️  No initial data available - will need to run scraper first")

    app.run(host='0.0.0.0', port=5001, debug=True)