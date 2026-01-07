# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Playlist Transcript & Gemini Refinement Extractor - A PyQt5 desktop application that extracts transcripts from YouTube playlists or individual videos and refines them using Google's Gemini API. The tool converts YouTube content into well-formatted, readable markdown documents suitable for NotebookLM, Obsidian, or other knowledge management tools.

## Core Architecture

### Single-File Application Structure
The entire application lives in `main.py` (~890 lines) with three main components:
- **MainWindow** (QMainWindow): GUI controller managing user inputs, file selection, and workflow orchestration
- **TranscriptExtractionThread** (QThread): Background worker for fetching YouTube transcripts via pytube and youtube-transcript-api
- **GeminiProcessingThread** (QThread): Background worker for AI-powered text refinement using Google Generative AI

### Threading Model
- GUI runs on main thread (PyQt5 event loop)
- Transcript extraction and Gemini processing run on separate QThreads to prevent UI freezing
- Threads communicate with MainWindow via PyQt signals: `progress_update`, `status_update`, `extraction_complete`, `error_occurred`, `processing_complete`
- Sequential workflow: extraction completes → triggers `start_gemini_processing()` → Gemini processing begins

### Data Flow
1. User provides YouTube URL (playlist or single video) + language + API key + output preferences
2. TranscriptExtractionThread:
   - Fetches video URLs from playlist (or single video)
   - Attempts to get English transcript first, falls back to any available language
   - Writes raw transcripts to intermediate .txt file
3. GeminiProcessingThread:
   - Splits each video transcript into configurable chunks (default 3000 words)
   - Sends chunks sequentially to Gemini API with context from previous chunk
   - Uses one of 5 refinement prompts based on user selection (main.py:25-76)
   - Writes refined output to final .txt file

### Refinement Styles & Prompts
Five prompt templates stored in `MainWindow.prompts` dictionary (main.py:25-76):
- **Balanced and Detailed**: Default, preserves all details with improved structure
- **Summary**: Concise overview, larger chunk size (10000 words)
- **Educational**: Textbook-like format with term definitions in blockquotes
- **Narrative Rewriting**: Transforms content into engaging narrative
- **Q&A Generation**: Creates foldable markdown Q&A for self-assessment

Each style has a suggested chunk size in `category_chunk_sizes` (main.py:77-83). All prompts use `[Language]` placeholder replaced at runtime.

### Configuration
- `.env` file for default API key and language (loaded via python-dotenv)
- Safety settings for Gemini API configured in GeminiProcessingThread.run() (main.py:776-781) - all harm categories set to BLOCK_NONE
- Available Gemini models hardcoded in `MainWindow.available_models` (main.py:89-91)

## Development Commands

### Running the Application
```bash
python main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Required Python Version
Python 3.9+ (uses PyQt5, pytube, youtube-transcript-api, google-generativeai, python-dotenv)

## Important Implementation Details

### API Error Handling
- Gemini API content safety blocks are caught via `ValueError` exception (main.py:823-828)
- When blocked, chunk is skipped with warning but processing continues
- Generic API errors stop processing and emit error signal

### Transcript Fetching Strategy
1. Always try English transcript first (`transcript_list_obj.find_transcript(['en'])`)
2. On NoTranscriptFound, fall back to first available language
3. If video has no transcripts at all, log error and continue to next video

### Chunk Processing with Context
Each Gemini chunk includes previous refined response as context to maintain coherence:
```python
context_prompt = f"Previous response:\n{previous_response}\n\nNew text to process..."
```
This prevents disconnected output across chunk boundaries.

### Progress Tracking
- Extraction progress: `(current_video / total_videos) * 100`
- Gemini progress: `(current_video / total_videos) * 100`
- Progress bar updates emitted via signals after each video completes

### Temporary Files
GeminiProcessingThread creates `{output_file}_temp_response.txt` to accumulate chunks per video, then appends to final output and clears temp file between videos.

## Common Patterns

### Adding a New Refinement Style
1. Add new prompt to `MainWindow.prompts` dict (main.py:25-76)
2. Add suggested chunk size to `category_chunk_sizes` (main.py:77-83)
3. Prompt must include `[Language]` placeholder for multi-language support
4. New style appears automatically in UI dropdown (QComboBox populated from prompts.keys())

### UI Styling
Dark theme implemented via PyQt5 stylesheets:
- `get_input_style()`, `get_button_style()`, `get_combobox_style()` methods
- Main colors: #2c3e50 (dark gray), #3498db (blue), #2ecc71 (green), #e74c3c (red)

### Thread Cancellation
Both threads have `_is_running` flag checked in processing loops. `cancel_processing()` sets flag to False, then quits and waits for threads to terminate.

## Edge Cases to Consider

- Videos without transcripts: Logged but don't stop processing
- Large playlists: No pagination, fetches all videos at once via pytube
- API rate limits: Not handled, relies on Gemini API quota
- Network errors: Caught generically, stop processing with error dialog
- Single video URLs: Detected by checking for "watch?v=" vs "playlist?list="
- Chunk size edge case: If last chunk < 500 words, merged with previous chunk (main.py:870-872)

## File Organization

```
.
├── main.py                    # Entire application (GUI + threads + logic)
├── requirements.txt           # Python dependencies
├── .env                       # Default API key and language (gitignored)
├── README.md                  # User-facing documentation
├── Example_Output.md          # Sample refined output
├── Example_Transcript.txt     # Sample raw transcript
├── LICENSE                    # MIT license
└── Images/                    # Screenshots for README
```

## Language Support

Application supports any language for output via the `output_language` parameter:
- User specifies language in GUI text input
- `[Language]` placeholder in prompts replaced with user input (main.py:805)
- Gemini generates all output in specified language
- Transcripts can be in any language (YouTube's available languages)
