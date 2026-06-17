# Balance Sheet QA System - Web UI

A web-based interface for the Balance Sheet QA System that allows you to upload balance sheets and ask questions about them using OpenRouter API.

## Features

✨ **Web Interface** - Clean, modern UI for uploading and questioning balance sheets
📄 **File Upload** - Support for PDF and TXT format balance sheets (up to 50MB)
🤖 **AI-Powered** - Powered by OpenRouter API with support for multiple models
💬 **Conversation** - Maintain conversation history with clear history reset button
📊 **Real-time Responses** - Get instant answers about your balance sheet

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

#### Windows PowerShell:
```powershell
$env:OPENROUTER_API_KEY="your_api_key_here"
```

#### Windows Command Prompt:
```cmd
set OPENROUTER_API_KEY=your_api_key_here
```

### 3. Run the Web Server

```bash
python app.py
```

The application will start at `http://127.0.0.1:5000`

### 4. Open in Browser

Navigate to `http://localhost:5000` in your web browser

## Usage

1. **Upload a Balance Sheet**
   - Click the upload area or drag-and-drop a PDF/TXT file
   - The system will process and index your document

2. **Ask Questions**
   - Type your question in the input field
   - Press Enter or click "Ask" button
   - Use `Ctrl+Enter` (Windows/Linux) or `Cmd+Enter` (macOS) to submit as well
   - Wait for the AI to analyze and respond

3. **Keyboard Shortcuts**
   - `Alt+R` to reset the conversation history
   - `Alt+E` to end the session

4. **Clear History**
   - Click "🔄 Clear History" to reset conversation history

## File Requirements

- **Formats**: PDF (.pdf) or Text (.txt)
- **Maximum Size**: 50MB
- **Content**: Should contain structured balance sheet data

## API Endpoints

### POST `/api/upload`
Upload a balance sheet file

**Parameters:**
- `file` (multipart/form-data): The balance sheet file

**Response:**
```json
{
  "success": true,
  "message": "Successfully loaded filename.pdf",
  "filename": "filename.pdf"
}
```

### POST `/api/ask`
Ask a question about the loaded document

**Request Body:**
```json
{
  "question": "What is the total assets?"
}
```

**Response:**
```json
{
  "success": true,
  "answer": "The total assets are...",
  "question": "What is the total assets?"
}
```

### POST `/api/reset`
Reset conversation history

**Response:**
```json
{
  "success": true,
  "message": "Conversation history cleared"
}
```

## Changing the Model

You can change the default OpenRouter model by setting the environment variable:

```powershell
$env:OPENROUTER_MODEL="openai/gpt-4o"
```

Available models:
- `meta-llama/llama-3-70b-instruct` (default, free)
- `openai/gpt-4o-mini`
- `google/gemini-pro-1.5`
- `mistralai/mixtral-8x7b-instruct`

See [OpenRouter Models](https://openrouter.ai/models) for full list.

## Project Structure

```
balance_sheet_qa_openrouter/
├── app.py                    # Flask web application
├── balance_sheet_qa.py       # Core QA logic
├── requirements.txt          # Python dependencies
├── templates/
│   └── index.html           # Main web interface
├── static/
│   ├── style.css            # Styling
│   └── script.js            # Frontend logic
└── uploads/                 # Uploaded files directory
```

## Troubleshooting

### "OPENROUTER_API_KEY environment variable is required"
- Set your OpenRouter API key as shown in Step 2

### "No endpoints found for model X"
- The model is not available with your API key
- Try changing to `meta-llama/llama-3-70b-instruct` (free tier)

### "Provider returned error (code=504)"
- The model provider is temporarily unavailable
- Try again in a few seconds
- Or switch to a different model

### Upload fails
- Check file size (max 50MB)
- Ensure file is PDF or TXT format
- Check browser console for detailed errors

## API Key Setup

1. Go to [OpenRouter](https://openrouter.ai)
2. Sign up or log in
3. Create/copy your API key from the dashboard
4. Set the `OPENROUTER_API_KEY` environment variable

## Notes

- Each file upload creates a new QA session
- Conversation history is maintained per session
- Maximum file size is 50MB
- The system works best with structured balance sheet data

## License

MIT
