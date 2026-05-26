NANOCODE_BRAIN=zai python ch04/nanocode_shared.py
NANOCODE_BRAIN=claude python ch04/nanocode_shared.py

# Quick Start Guide - Z.ai Coding Plan Integration

## 🚀 Setup in 3 Steps

### 1. Configure Environment

```bash
cd ch04
cp .env.example .env
```

Edit `.env` and add your Z.ai API key:
```env
NANOCODE_BRAIN=zai
ZAI_CODING_API_KEY=your_actual_key_here
```

### 2. Install Dependencies

```bash
pip install python-dotenv requests
```

### 3. Run Tests (Optional)

```bash
python test_zai_integration.py
```

## 🎯 Run the Agent

```bash
python nanocode_zai.py
```

## 📝 Example Session

```
⚡ Nanocode v0.4 - Z.ai Edition
Commands: /q quit, /switch toggle brain
Brain: zai

🤖 Z.ai Coding Plan initialized:
   Model: GLM-4.7
   URL: https://api.z.ai/api/coding/paas/v4/messages
   Proxy: Disabled

[zai] ❯ Write a Python function to calculate fibonacci numbers

[Z.ai responds with code and explanation]

[zai] ❯ /switch
Switched to: claude

[claude] ❯ /switch
Switched to: deepseek

[deepseek] ❯ /switch
Switched to: zai

[zai] ❯ /q
Exiting...
```

## 🔧 Configuration Options

### Use Different Model

Edit `.env`:
```env
ZAI_CODING_MODEL=GLM-4.5
```

### Use Local Proxy (for debugging)

Edit `.env`:
```env
ZAI_CODING_USE_PROXY=true
ZAI_CODING_PROXY_URL=http://localhost:8080/api/coding/paas/v4/messages
```

### Switch API Provider

Edit `.env`:
```env
NANOCODE_BRAIN=claude    # Use Claude
NANOCODE_BRAIN=deepseek  # Use DeepSeek
NANOCODE_BRAIN=zai       # Use Z.ai Coding Plan
```

## 🐛 Troubleshooting

**Problem**: "ZAI_CODING_API_KEY not found"
**Solution**: Make sure `.env` file exists and contains your API key

**Problem**: Connection timeout
**Solution**: Check internet connection or try proxy mode

**Problem**: Unexpected responses
**Solution**: Run `python test_zai_integration.py` to diagnose

## 📚 Files Overview

- `nanocode_zai.py` - Main agent with Z.ai integration
- `test_zai_integration.py` - Test suite
- `.env.example` - Environment template
- `README_ZAI.md` - Full documentation
- `USAGE.md` - This quick start guide
