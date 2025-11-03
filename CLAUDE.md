# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a ComfyUI plugin for BizyAIR AI applications (comfyui_bizyair) that provides custom nodes for integrating with the BizyAIR API service. The plugin allows users to remotely call AI services through BizyAIR's web API.

## Architecture

The plugin follows the standard ComfyUI custom node architecture:

### Core Components

- **BizyAIR.py**: Main plugin file containing all node classes and utility functions
- **__init__.py**: ComfyUI plugin initialization with node mappings and display names
- **check_requirements.py**: Utility script for checking Python package dependencies
- **requirements.txt**: Minimal dependencies list (httpx, requests, openai)

### Node Classes

The plugin implements 6 main node types:

1. **BA_BizyAIR_Main**: Primary API interface node for making web app requests
2. **BA_LoadImage**: Image input node supporting both base64 and URL modes
3. **BA_Float_Value**: Numeric input node with float/integer options
4. **BA_String_Value**: Text input node for string parameters
5. **BA_Image_Resizer**: Image preprocessing node for size adjustment
6. **BA_Task_Status_Checker**: Node for checking async task status

### Key Utilities

- **Image Processing**: Functions for converting between tensors, PIL images, and base64 encoding
- **API Communication**: HTTP client for BizyAIR API integration with proper error handling
- **Caching System**: Local image caching to avoid repeated downloads
- **Format Handling**: Automatic conversion between different image formats (WebP preferred)

## Development Commands

### Dependencies Management
```bash
# Check package requirements and versions
python check_requirements.py

# Install dependencies (if needed)
pip install -r requirements.txt
```

### Testing
No formal test suite is currently implemented. Testing is done through ComfyUI interface.

## Configuration

### API Key Setup
The plugin looks for API keys in:
1. `key/siliconflow_API_key.txt` (relative to plugin directory)
2. Manual input through node parameters

### Image Caching
Images downloaded from URLs are cached in ComfyUI's temp directory using MD5 hashes of URLs.

## Important Notes

- Plugin uses Chinese category names: "🇨🇳BOZO/BizyAir" and "🇨🇳BOZO/PIC"
- Image format is standardized to WebP for API communication
- All tensor operations assume [batch, height, width, channels] format
- Error handling includes detailed logging for troubleshooting API failures
- The plugin supports both synchronous API calls and async task status checking

## File Structure Notes

- No build scripts or Makefiles - this is a pure Python plugin
- Key directory exists but is gitignored for security
- Web directory reference exists but no web files are present
- Plugin follows ComfyUI's standard node registration pattern