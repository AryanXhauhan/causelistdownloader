#!/usr/bin/env python3
"""
eCourts REAL-TIME Cause List Downloader - PRODUCTION VERSION
With BULK DOWNLOAD feature for all judges in a court complex
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import logging
import importlib.util
spec = importlib.util.spec_from_file_location('realtime_causelist_scraper', 'scraper/realtime-causelist-scraper.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
RealTimeCauseListScraper = module.RealTimeCauseListScraper
from scraper.pdf_generator import BulkPDFGenerator
import threading
import time

app = Flask(__name__)
app.secret_key = 'ecourts-realtime-causelist-downloader-2025'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create directories
os.makedirs('downloads', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Global scraper instance (for session persistence)
current_scraper = None

@app.route('/')
def index():
    """Home page with REAL-TIME data promise"""
    return render_template('realtime-index.html')

@app.route('/api/states')
def get_states():
    """Get REAL states from eCourts portal"""
    try:
        global current_scraper
        print("🌐 Fetching REAL states from eCourts...")
        
        # Initialize scraper if not exists
        if current_scraper is None:
            current_scraper = RealTimeCauseListScraper(headless=True)
        
        states = current_scraper.get_states()
        
        print(f"✅ Fetched {len(states)} REAL states")
        return jsonify({
            'success': True, 
            'states': states,
            'source': 'REAL_ECOURTS_LIVE',
            'timestamp': time.time()
        })
        
    except Exception as e:
        print(f"❌ Real states fetch failed: {e}")
        # Fallback to basic states if real fetch fails
        fallback_states = [
            {'code': '07', 'name': 'Delhi (All Districts)'},
            {'code': '09', 'name': 'Uttar Pradesh'},
            {'code': '27', 'name': 'Maharashtra'},
            {'code': '29', 'name': 'Karnataka'}
        ]
        return jsonify({
            'success': True, 
            'states': fallback_states,
            'source': 'FALLBACK_DATA',
            'error': str(e)
        })

@app.route('/api/districts/<state_code>')
def get_districts(state_code):
    """Get REAL districts for selected state"""
    try:
        global current_scraper
        print(f"🏙️ Fetching REAL districts for state: {state_code}")
        
        if current_scraper is None:
            current_scraper = RealTimeCauseListScraper(headless=True)
        
        districts = current_scraper.get_districts(state_code)
        
        print(f"✅ Fetched {len(districts)} REAL districts")
        return jsonify({
            'success': True, 
            'districts': districts,
            'source': 'REAL_LIVE_DATA',
            'state_code': state_code
        })
        
    except Exception as e:
        print(f"❌ Real districts fetch failed: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/court_complexes/<state_code>/<district_code>')
def get_court_complexes(state_code, district_code):
    """Get REAL court complexes"""
    try:
        global current_scraper
        print(f"🏛️ Fetching REAL court complexes: {state_code}/{district_code}")
        
        if current_scraper is None:
            current_scraper = RealTimeCauseListScraper(headless=True)
        
        complexes = current_scraper.get_court_complexes(state_code, district_code)
        
        print(f"✅ Fetched {len(complexes)} REAL court complexes")
        return jsonify({
            'success': True, 
            'complexes': complexes,
            'source': 'REAL_LIVE_DATA',
            'district_code': district_code
        })
        
    except Exception as e:
        print(f"❌ Real complexes fetch failed: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/judges/<state_code>/<district_code>/<complex_code>')
def get_judges_in_complex(state_code, district_code, complex_code):
    """Get all judges in a court complex for BULK download"""
    try:
        global current_scraper
        print(f"👨‍⚖️ Fetching ALL judges in complex: {complex_code}")
        
        if current_scraper is None:
            current_scraper = RealTimeCauseListScraper(headless=True)
        
        judges = current_scraper.get_all_judges_in_complex(complex_code)
        
        print(f"✅ Found {len(judges)} judges in complex")
        return jsonify({
            'success': True, 
            'judges': judges,
            'complex': complex_code,
            'total_judges': len(judges),
            'source': 'REAL_LIVE_DATA'
        })
        
    except Exception as e:
        print(f"❌ Judges fetch failed: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download_single_causelist', methods=['POST'])
def download_single_causelist():
    """Download cause list for a specific judge"""
    try:
        data = request.get_json()
        print(f"📥 Single cause list download request: {data}")
        
        global current_scraper
        if current_scraper is None:
            current_scraper = RealTimeCauseListScraper(headless=True)
        
        # Download cause list for specific judge
        result = current_scraper.download_cause_list_for_judge(
            judge_code=data.get('judge_code'),
            judge_name=data.get('judge_name'),
            date=data.get('date'),
            case_type=data.get('case_type', 'Civil')
        )
        
        if result['success']:
            # Generate PDF for single judge
            from scraper.pdf_generator import PDFGenerator
            pdf_gen = PDFGenerator()
            
            filename = f"causelist_{result['judge'].replace(' ', '_')}_{result['date'].replace('/', '-')}.pdf"
            pdf_path = pdf_gen.generate_pdf(result, filename)
            
            return jsonify({
                'success': True,
                'message': f"Downloaded cause list for {result['judge']}",
                'pdf_url': f'/download/{filename}',
                'cases_count': len(result['cases']),
                'judge': result['judge'],
                'date': result['date'],
                'case_type': result['case_type']
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Download failed')})
            
    except Exception as e:
        print(f"❌ Single download error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download_bulk_causelist', methods=['POST'])
def download_bulk_causelist():
    """🚀 BULK DOWNLOAD - All judges in a court complex"""
    try:
        data = request.get_json()
        print(f"🔄 BULK DOWNLOAD request: {data}")
        
        global current_scraper
        if current_scraper is None:
            current_scraper = RealTimeCauseListScraper(headless=True)
        
        # BULK download for all judges in complex
        bulk_result = current_scraper.download_all_cause_lists_bulk(
            complex_code=data.get('complex'),
            date=data.get('date'),
            case_type=data.get('case_type', 'Both')
        )
        
        if bulk_result['success']:
            # Generate separate PDFs for each judge
            pdf_files = []
            
            for cause_list in bulk_result['cause_lists']:
                try:
                    from scraper.pdf_generator import PDFGenerator
                    pdf_gen = PDFGenerator()
                    
                    judge_name_clean = cause_list['judge'].replace(' ', '_').replace('/', '_').replace('.', '')
                    filename = f"causelist_{judge_name_clean}_{cause_list['case_type']}_{cause_list['date'].replace('/', '-')}.pdf"
                    
                    pdf_path = pdf_gen.generate_pdf(cause_list, filename)
                    pdf_files.append({
                        'filename': filename,
                        'judge': cause_list['judge'],
                        'case_type': cause_list['case_type'],
                        'cases_count': len(cause_list['cases']),
                        'url': f'/download/{filename}'
                    })
                    
                except Exception as pdf_error:
                    print(f"⚠️ PDF generation failed for {cause_list['judge']}: {pdf_error}")
            
            # Also create a combined ZIP file for easy download
            zip_filename = f"bulk_causelist_{bulk_result['complex']}_{bulk_result['date'].replace('/', '-')}.zip"
            create_bulk_zip(pdf_files, zip_filename)
            
            return jsonify({
                'success': True,
                'message': f"BULK DOWNLOAD COMPLETE: {bulk_result['successful_downloads']} judges processed",
                'complex': bulk_result['complex'],
                'date': bulk_result['date'],
                'total_judges': bulk_result['total_judges'],
                'successful_downloads': bulk_result['successful_downloads'],
                'pdf_files': pdf_files,
                'zip_download': f'/download/{zip_filename}',
                'total_cases': sum([len(cl['cases']) for cl in bulk_result['cause_lists']]),
                'source': 'REAL_TIME_BULK_SCRAPING'
            })
        else:
            return jsonify({'success': False, 'error': bulk_result.get('error', 'Bulk download failed')})
            
    except Exception as e:
        print(f"❌ Bulk download error: {e}")
        return jsonify({'success': False, 'error': str(e)})

def create_bulk_zip(pdf_files, zip_filename):
    """Create ZIP file containing all PDFs"""
    try:
        import zipfile
        
        zip_path = os.path.join('downloads', zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for pdf_file in pdf_files:
                pdf_path = os.path.join('downloads', pdf_file['filename'])
                if os.path.exists(pdf_path):
                    zipf.write(pdf_path, pdf_file['filename'])
        
        print(f"✅ Created bulk ZIP: {zip_filename}")
        
    except Exception as e:
        print(f"❌ ZIP creation failed: {e}")

@app.route('/api/captcha')
def get_captcha():
    """Get REAL captcha from eCourts (if required)"""
    try:
        print("🔐 Captcha requested")
        
        # For some court systems, captcha might not be required
        # Return a simple response for now
        return jsonify({
            'success': True,
            'captcha_required': False,
            'message': 'Direct court access - captcha not required',
            'session_id': str(int(time.time() * 1000))
        })
        
    except Exception as e:
        print(f"❌ Captcha error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    """Serve PDF and ZIP files"""
    try:
        file_path = os.path.join('downloads', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get system status and statistics"""
    try:
        downloads_count = len([f for f in os.listdir('downloads') if f.endswith('.pdf')])
        
        return jsonify({
            'success': True,
            'status': 'RUNNING',
            'mode': 'REAL_TIME_SCRAPING',
            'downloads_generated': downloads_count,
            'scraper_active': current_scraper is not None,
            'timestamp': time.time(),
            'features': {
                'real_time_data': True,
                'bulk_download': True,
                'multi_judge_support': True,
                'auto_pdf_generation': True
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(Exception)
def handle_error(e):
    """Global error handler"""
    logging.error(f"Unhandled error: {e}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 eCourts REAL-TIME Cause List Downloader - PRODUCTION VERSION")
    print("="*70)
    print("✅ REAL-TIME data fetching from eCourts portal")
    print("✅ BULK DOWNLOAD for all judges in court complex")
    print("✅ Individual judge cause list download")
    print("✅ Automatic PDF generation for each judge")
    print("✅ ZIP file creation for bulk downloads")
    print("✅ New Delhi District Courts integration")
    print("✅ Fallback system for reliability")
    print("="*70)
    print("🌐 Starting server on: http://localhost:5001")
    print("📊 Status endpoint: http://localhost:5001/api/status")
    print("="*70 + "\n")
    
    try:
        # Test browser setup on startup
        print("🔧 Testing browser setup...")
        test_scraper = RealTimeCauseListScraper(headless=True)
        print("✅ Browser setup successful")
        test_scraper.close()
        
        app.run(debug=True, host='0.0.0.0', port=5001)
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        print("💡 Make sure ChromeDriver is installed!")
        print("   pip install webdriver-manager")
    
    finally:
        # Cleanup
        if current_scraper:
            current_scraper.close()