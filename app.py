"""
Flask web application for Balance Sheet QA System
Wraps balance_sheet_qa.py with a web UI for file upload and questioning
"""

import os
import json
import threading
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from balance_sheet_qa import BalanceSheetQA

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'txt'}

# Global QA instance (one per session in production, use session management)
qa_instance = None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and initialize QA system."""
    global qa_instance
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF and TXT files are allowed'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Initialize or reinitialize QA system
        qa_instance = BalanceSheetQA()
        qa_instance.load(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Successfully loaded {filename}',
            'filename': filename
        }), 200
    
    except ValueError as e:
        return jsonify({'error': f'Configuration error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Handle question and return answer."""
    global qa_instance
    
    if qa_instance is None:
        return jsonify({'error': 'No document loaded. Please upload a balance sheet first.'}), 400
    
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    
    question = data['question'].strip()
    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400
    
    try:
        answer = qa_instance.ask(question)
        return jsonify({
            'success': True,
            'answer': answer,
            'question': question
        }), 200
    
    except RuntimeError as e:
        return jsonify({'error': f'API error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500


@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation history."""
    global qa_instance
    
    if qa_instance is None:
        return jsonify({'error': 'No document loaded'}), 400
    
    qa_instance.reset_history()
    return jsonify({'success': True, 'message': 'Conversation history cleared'}), 200


@app.route('/api/shutdown', methods=['POST'])
def shutdown_server():
    """Gracefully shutdown the server."""
    def shutdown():
        import time
        time.sleep(1)  # Give response time to send
        os.kill(os.getpid(), 15)  # Send SIGTERM to gracefully stop
    
    thread = threading.Thread(target=shutdown)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Server shutting down...'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
