# Implementation Plan: Multi-Provider AI Support & Pink/Purple Color Scheme

## Overview
Add support for Claude, ChatGPT, and Gemini AI providers with GUI provider selection, and update the color scheme from blue to pink/purple tones.

## User Requirements
1. ✅ Provider dropdown in GUI to select between Claude, ChatGPT, and Gemini per run
2. ✅ Store all three API keys in .env file (GEMINI_API_KEY, CLAUDE_API_KEY, CHATGPT_API_KEY)
3. ✅ Design cohesive pink/purple color palette to replace blue tones
4. ✅ Use one global chunk size for all providers
5. ✅ Maintain .env as git-ignored

## Pink/Purple Color Palette

| Old Color | Usage | New Color | Name |
|-----------|-------|-----------|------|
| `#2c3e50` | Main backgrounds | `#1a0d1f` | Deep Purple |
| `#34495e` | Input backgrounds | `#2d1b3d` | Dark Plum |
| `#3498db` | Borders/accents | `#c74b94` | Bright Pink |
| `#2ecc71` | Success/progress | `#d946ef` | Purple |
| `#e74c3c` | Errors/cancel | `#f472b6` | Light Pink |
| `#7f8c8d` | Disabled states | `#6b4f7a` | Muted Purple |
| `#ecf0f1` | Light text | `#f8e7f5` | Pale Pink |
| `#bdc3c7` | Secondary text | `#d4a5d4` | Lavender |

**Gradients:**
- Primary: `#c74b94` → `#d946ef`
- Success: `#d946ef` → `#a855f7`
- Cancel: `#f472b6` → `#ec4899`

## Implementation Steps

### 1. Update Dependencies
**File:** `requirements.txt`

Add:
```
anthropic
openai
```

### 2. Add Provider Abstraction Classes
**File:** `main.py` (insert before MainWindow class, around line 18)

Create:
- `AIProvider` (abstract base class with configure(), generate_content(), get_available_models(), handle_error())
- `GeminiProvider` (refactored from existing code, includes safety_settings)
- `ClaudeProvider` (uses anthropic library, messages.create() API)
- `ChatGPTProvider` (uses openai library, chat.completions.create() API)
- `AIProviderFactory` (creates provider instances based on name)

**Model Lists:**
- Gemini: "gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.0-flash",
- Claude: "claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001", "claude-opus-4-5-20251101",
- ChatGPT: "gpt-5.2-2025-12-11", "gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07"

### 3. Update MainWindow.__init__
**File:** `main.py` (lines 21-94)

Changes:
- Add `self.selected_provider = "ChatGPT"`
- Remove `self.available_models` (now provider-specific)
- Add `self.current_provider = None`

### 4. Update Color Scheme
**File:** `main.py` (multiple locations)

**Methods to update:**
- `get_combobox_style()` (lines 96-144): Replace all color hex codes
- `get_input_style()` (lines 394-407): Replace all color hex codes
- `apply_dark_mode()` (lines 431-439): Replace background and text colors
- `get_button_style()` (lines 409-429): Callers updated to use new gradient colors

**Inline stylesheets to update:**
- Title label gradient (line 177-179): Use `#1a0d1f` → `#c74b94`
- Progress bar (lines 313-327): Use `#c74b94` and `#d946ef`
- Status display (lines 333-340): Use new colors
- All button calls: Update color parameters

### 5. Add Provider Selection UI
**File:** `main.py` (around line 229, after refinement style dropdown)

Add:
```python
# AI Provider Selection
provider_layout = QVBoxLayout()
provider_label = QLabel("AI Provider:")
self.provider_combo = QComboBox()
self.provider_combo.addItems(["Gemini", "Claude", "ChatGPT"])
self.provider_combo.setCurrentText("Gemini")
self.provider_combo.currentIndexChanged.connect(self.provider_changed)
```

New method `provider_changed()`:
- Updates API key label (e.g., "Gemini API Key:" → "Claude API Key:")
- Updates API key placeholder text
- Loads saved API key for selected provider from .env
- Updates selected model to first available for provider

### 6. Update API Key Input
**File:** `main.py` (lines 286-300)

Changes:
- Make label dynamic: `self.api_key_label = QLabel("Gemini API Key:")`
- Update label/placeholder when provider changes
- Load API key using new `get_api_key_for_provider()` helper
- Remove the input box for the API_KEY in the UI

New helper method:
```python
def get_api_key_for_provider(self, provider_name):
    key_mapping = {
        "Gemini": os.environ.get("GEMINI_API_KEY", os.environ.get("API_KEY", "")),  # Backward compatible
        "Claude": os.environ.get("CLAUDE_API_KEY", ""),
        "ChatGPT": os.environ.get("CHATGPT_API_KEY", "")
    }
    return key_mapping.get(provider_name, "")
```

### 7. Update Window Titles
**File:** `main.py` (lines 160, 170)

Change from:
- "YouTube Playlist Transcript & **Gemini** Refinement Extractor"

To:
- "YouTube Playlist Transcript & **AI** Refinement Extractor"

### 8. Update Model Selection Dialog
**File:** `main.py` (lines 508-532)

Rename: `select_gemini_model()` → `select_ai_model()`

Changes:
- Get current provider from dropdown
- Use factory to create temp provider instance
- Get available models from provider
- Update dialog title: "Select {provider_name} Model"

### 9. Refactor Processing Thread
**File:** `main.py` (lines 744-883)

Rename: `GeminiProcessingThread` → `AIProcessingThread`

**Constructor changes:**
- Add `provider_name` parameter
- Store provider name for factory creation

**run() method changes:**
- Remove direct `genai.configure()` call
- Create provider: `self.provider = AIProviderFactory.create_provider(self.provider_name, self.api_key, self.selected_model_name)`
- Call `self.provider.configure()`
- Replace `model.generate_content()` with `self.provider.generate_content(full_prompt)`
- Update error handling to use `self.provider.handle_error()`

**Error handling updates:**
```python
try:
    response_text = self.provider.generate_content(full_prompt)
except ValueError as e:
    # Gemini content blocked
    error_msg = self.provider.handle_error(e)
    self.status_update.emit(f"<font color='#f472b6'>Warning: {error_msg}. Skipping chunk.</font>")
    continue
except Exception as e:
    error_msg = self.provider.handle_error(e)
    self.error_occurred.emit(error_msg)
    return
```

### 10. Update Processing Flow
**File:** `main.py` (lines 534-588)

**In `start_extraction_and_refinement()`:**
- Call `select_ai_model()` instead of `select_gemini_model()`
- Pass `self.selected_provider` to processing thread

**Rename method:** `start_gemini_processing()` → `start_ai_processing()`

**Update status messages:**
- Replace "Gemini" references with provider-agnostic text or use current provider variable

### 11. Update Validation
**File:** `main.py` (lines 447-496)

In `validate_inputs()`:
- Get current provider name
- Update error message: "Please enter your {provider_name} API key"

### 12. Update .env File Structure
**File:** `.env.example`

Update to:
```bash
# AI Provider API Keys
GEMINI_API_KEY=
CLAUDE_API_KEY=
CHATGPT_API_KEY=

# Legacy support (backward compatible)
API_KEY=

# Default Settings
LANGUAGE=en_US.UTF-8
```

### 13. Add Required Imports
**File:** `main.py` (lines 1-17)

Add:
```python
import anthropic
import openai
from abc import ABC, abstractmethod
```

## Critical Files to Modify

1. `/Users/lennart.querter/go/src/github.com/Youtube-playlist-to-formatted-text/main.py` - All implementation changes
2. `/Users/lennart.querter/go/src/github.com/Youtube-playlist-to-formatted-text/requirements.txt` - Add anthropic, openai
3. `/Users/lennart.querter/go/src/github.com/Youtube-playlist-to-formatted-text/.env` - Add new API key fields

## Testing Checklist

- [ ] Install new dependencies (anthropic, openai)
- [ ] Verify color scheme is consistent across all UI elements
- [ ] Test provider dropdown switches API key field correctly
- [ ] Test each provider with a small YouTube video
- [ ] Verify model selection shows provider-specific models
- [ ] Test error handling for invalid API keys
- [ ] Verify backward compatibility with old .env format (API_KEY → GEMINI_API_KEY)
- [ ] Test all 5 refinement styles with each provider
- [ ] Verify progress tracking works with all providers

## Implementation Notes

- Maintain single-file architecture (all classes in main.py)
- Each provider handles its own API-specific error types
- Provider abstraction keeps core processing logic unchanged
- Backward compatibility: old `API_KEY` env var maps to `GEMINI_API_KEY`
- Default provider on first run: Gemini (existing behavior)
