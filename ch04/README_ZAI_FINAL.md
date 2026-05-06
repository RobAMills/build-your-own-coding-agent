# Z.ai Coding Plan Integration - Direct API Mode

## ✅ Working Configuration

The Z.ai Coding Plan integration now works **directly** without requiring mitmproxy proxy.

## 🚀 Quick Start

### 1. Configure Environment
```bash
cd ch04
cp .env.example .env
```

Edit `.env` and add your Z.ai API key:
```env
NANOCODE_BRAIN=zai
ZAI_CODING_API_KEY=your_actual_zai_api_key_here
ZAI_CODING_MODEL=GLM-4.7
```

### 2. Run the Agent
```bash
python3 nanocode_zai.py
```

## 🔧 Technical Details

### Correct API Endpoint

Based on analysis of successful requests in logs, the correct endpoint is:
```
https://api.z.ai/api/anthropic/v1/messages
```

**NOT** `/api/coding/paas/v4/messages` (that's the internal endpoint that the proxy forwards to).

### Authentication Headers

Z.ai uses **Anthropic-compatible authentication**:
```python
headers = {
    "x-api-key": self.api_key,           # ✅ Correct
    "anthropic-version": "2023-06-01",   # ✅ Required
    "content-type": "application/json"
}
```

**NOT** `Authorization: Bearer {token}` (that was the bug).

### Request Format

Standard Anthropic message format works:
```json
{
  "model": "GLM-4.7",
  "max_tokens": 16000,
  "messages": [
    {"role": "user", "content": "hello"}
  ]
}
```

## 🐛 Issues Fixed

### ❌ Previous Issues:
1. **Wrong authentication**: Used `Authorization: Bearer` instead of `x-api-key`
2. **Wrong endpoint**: Tried `/api/coding/paas/v4/messages` instead of `/api/anthropic/v1/messages`
3. **Unnecessary proxy**: Required mitmproxy when direct API access works

### ✅ Current Solution:
1. **Correct authentication**: Uses `x-api-key` header
2. **Correct endpoint**: Uses Anthropic-compatible endpoint
3. **Direct API access**: No proxy required

## 🎯 How It Works

1. **Direct Connection**: nanocode connects directly to `https://api.z.ai/api/anthropic/v1/messages`
2. **Anthropic Compatibility**: Uses standard Anthropic API format
3. **GLM Models**: Uses Z.ai's GLM-4.7 model (configurable)
4. **Standard Responses**: Compatible with Anthropic response format

## 🔍 Configuration Options

### Environment Variables
```env
# Required
ZAI_CODING_API_KEY=your_key_here

# Optional (with defaults)
NANOCODE_BRAIN=zai                    # Select brain
ZAI_CODING_MODEL=GLM-4.7              # Model selection
ZAI_CODING_BASE_URL=https://api.z.ai  # API base URL
ZAI_CODING_PATH=/api/anthropic/v1/messages  # Endpoint path
```

### Available Models
- `GLM-4.7` (default, most capable)
- `GLM-4.5` (faster)
- `GLM-4.0` (fastest)

## 📊 Testing

### Run Test Suite
```bash
python3 test_zai_integration.py
```

### Manual Test
```python
from nanocode_zai import ZaiCoding
brain = ZaiCoding()
conversation = [{"role": "user", "content": "Say 'Hello, Z.ai!'"}]
thought = brain.think(conversation)
print(f"Response: {thought.text}")
```

## 🔄 Brain Switching

Switch between different LLM providers:
```
[zai] ❯ /switch
Switched to: claude

[claude] ❯ /switch  
Switched to: deepseek

[deepseek] ❯ /switch
Switched to: zai
```

## 📝 Implementation Details

### Key Components

**ZaiCoding Class**:
```python
class ZaiCoding(Brain):
    def __init__(self):
        self.api_key = os.getenv("ZAI_CODING_API_KEY")
        self.url = "https://api.z.ai/api/anthropic/v1/messages"
        self.model = "GLM-4.7"
    
    def think(self, conversation):
        # Uses Anthropic-compatible headers and format
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        # Standard request format
        payload = {
            "model": self.model,
            "max_tokens": 16000,
            "messages": conversation
        }
```

### Response Parsing

Robust parsing handles multiple response formats:
- Anthropic-style content arrays
- OpenAI-style choices  
- Plain text responses
- Tool use blocks
- Thinking blocks

## 🚨 Troubleshooting

### "invalid x-api-key" error
**Cause**: Wrong API key or authentication format  
**Fix**: Verify `ZAI_CODING_API_KEY` in `.env`

### 404 errors  
**Cause**: Wrong API endpoint  
**Fix**: Ensure default endpoint `https://api.z.ai/api/anthropic/v1/messages`

### Empty responses
**Cause**: Response parsing mismatch  
**Fix**: Check response format in debug logs

### Connection timeout
**Cause**: Network issues  
**Fix**: Check internet connectivity and API status

## ✅ Summary

The Z.ai Coding Plan integration is **fully functional** with:
- ✅ Direct API access (no proxy needed)
- ✅ Correct Anthropic-compatible authentication
- ✅ Proper endpoint configuration
- ✅ Robust response parsing
- ✅ Brain switching support
- ✅ Tool calling compatibility

The agent now works seamlessly with Z.ai's GLM models while maintaining compatibility with the existing nanocode architecture.
