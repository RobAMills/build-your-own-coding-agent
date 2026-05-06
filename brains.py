"""
Shared Brain Module for Nanocode Agents
Provides reusable LLM provider implementations across all chapters.

Based on proven implementation from ch04/nanocode_zai.py
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


# --- HTTP Helpers ---

def request_with_retry(url, headers, payload, max_retries=10):
    """Make HTTP POST with retry on rate limit (429), server errors (5xx), and network failures."""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
        except requests.exceptions.RequestException as e:
            wait_time = 2 ** attempt
            print(f"Network error: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            continue

        if response.status_code == 429 or response.status_code >= 500:
            retry_after = response.headers.get("retry-after")
            try:
                wait_time = int(retry_after) if retry_after else 2 ** attempt
            except (ValueError, TypeError):
                wait_time = 2 ** attempt
            print(f"Error {response.status_code}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            continue

        if response.status_code >= 400:
            try:
                error_msg = response.json()["error"]["message"]
            except (KeyError, ValueError):
                error_msg = response.text
            raise Exception(f"API error ({response.status_code}): {error_msg}")

        return response

    raise Exception(f"Request failed after {max_retries} retries")


# --- Exceptions ---

class AgentStop(Exception):
    """Raised when the agent should stop processing."""
    pass


# --- Brain Response Types ---

class ToolCall:
    """A tool invocation request from the brain."""

    def __init__(self, id, name, args):
        self.id = id
        self.name = name
        self.args = args  # dict


class Thought:
    """Standardized response from any Brain."""

    def __init__(self, text=None, tool_calls=None, thinking=None):
        self.text = text  # str or None
        self.tool_calls = tool_calls or []  # list of ToolCall
        self.thinking = thinking  # str or None


# --- Brain Interface ---

class Brain:
    """Base class for LLM providers."""

    def think(self, conversation):
        """Process conversation, return Thought."""
        raise NotImplementedError

    def _parse_response(self, content):
        """Convert API response format to Thought."""
        text_parts = []
        tool_calls = []
        thinking = None

        for block in content:
            if block["type"] == "thinking":
                thinking = block["thinking"]
            elif block["type"] == "text":
                text_parts.append(block["text"])
            elif block["type"] == "tool_use":
                tool_calls.append(ToolCall(
                    id=block["id"],
                    name=block["name"],
                    args=block["input"]
                ))

        return Thought(
            text="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
            thinking=thinking
        )


# --- Claude ---

class Claude(Brain):
    """Claude API - the brain of our agent."""

    def __init__(self, **kwargs):
        """Initialize Claude brain.
        
        Accepts **kwargs for compatibility with different chapter requirements:
        - ch04: No parameters
        - ch05: tools=None
        - ch06+: memory=None, tools=None
        """
        # Handle optional parameters for chapter compatibility
        self.tools = kwargs.get('tools', [])
        self.memory = kwargs.get('memory', None)
        
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env")
        self.model = "claude-sonnet-4-6"
        self.url = "https://api.anthropic.com/v1/messages"

    def think(self, conversation):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 16000,
            "messages": conversation
        }
        if self.tools:
            payload["tools"] = self.tools

        response = request_with_retry(self.url, headers, payload)
        return self._parse_response(response.json()["content"])


# --- DeepSeek ---

class DeepSeek(Brain):
    """DeepSeek API (Anthropic-compatible, with tool support)."""

    def __init__(self, **kwargs):
        """Initialize DeepSeek brain.
        
        Accepts **kwargs for compatibility with different chapter requirements.
        """
        self.tools = kwargs.get('tools', [])
        self.memory = kwargs.get('memory', None)
        
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in .env")
        self.model = "deepseek-chat"
        self.url = "https://api.deepseek.com/anthropic/v1/messages"

    def think(self, conversation):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": conversation
        }
        if self.tools:
            payload["tools"] = self.tools

        response = request_with_retry(self.url, headers, payload)
        return self._parse_response(response.json()["content"])


# --- Z.ai Coding Plan ---

class ZaiCoding(Brain):
    """Z.ai Coding Plan API (Anthropic-compatible endpoint)."""

    def __init__(self, **kwargs):
        """Initialize Z.ai Coding brain.
        
        Accepts **kwargs for compatibility with different chapter requirements:
        - ch04: No parameters
        - ch05: tools=None
        - ch06+: memory=None, tools=None
        """
        # Handle optional parameters for chapter compatibility
        self.tools = kwargs.get('tools', [])
        self.memory = kwargs.get('memory', None)
        
        self.api_key = os.getenv("ZAI_CODING_API_KEY")
        if not self.api_key:
            raise ValueError("ZAI_CODING_API_KEY not found in .env")
        
        base_url = os.getenv("ZAI_CODING_BASE_URL", "https://api.z.ai")
        endpoint_path = os.getenv("ZAI_CODING_PATH", "/api/anthropic/v1/messages")
        self.url = base_url + endpoint_path
        self.model = os.getenv("ZAI_CODING_MODEL", "GLM-4.7")
        
        print(f"🤖 Z.ai Coding Plan initialized:")
        print(f"   Model: {self.model}")
        print(f"   URL: {self.url}")

    def think(self, conversation):
        """Process conversation with Z.ai Coding Plan API."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 16000,
            "messages": conversation
        }
        
        # Add tools if available (for ch05+)
        if self.tools:
            payload["tools"] = self.tools

        try:
            response = request_with_retry(self.url, headers, payload)
            return self._parse_zai_response(response.json())
        except Exception as e:
            print(f"❌ Z.ai API Error: {e}")
            raise

    def _parse_zai_response(self, response_data):
        """Parse Z.ai Coding Plan API response format.
        
        Handles multiple potential response formats:
        1. Anthropic-compatible format with 'content' array
        2. Direct format with inline content
        3. Alternative formats with different structures
        """
        # Try Anthropic-compatible format first
        if "content" in response_data:
            return self._parse_response(response_data["content"])
        
        # Fallback: try to find content in different locations
        content = response_data.get("content", [])
        
        # If content is not a list, try to convert it
        if not isinstance(content, list):
            # Handle alternative response formats
            if "message" in response_data:
                content = [{"type": "text", "text": response_data["message"]}]
            elif "choices" in response_data:
                # OpenAI-style format
                choice = response_data["choices"][0]
                content = [{"type": "text", "text": choice.get("message", {}).get("content", "")}]
            else:
                content = [{"type": "text", "text": str(response_data)}]
        
        # Parse the content
        return self._parse_response(content)


# --- Available Brains Dictionary ---

BRAINS = {
    "claude": Claude,
    "deepseek": DeepSeek,
    "zai": ZaiCoding,
}


__all__ = [
    'request_with_retry',
    'AgentStop',
    'ToolCall',
    'Thought',
    'Brain',
    'Claude',
    'DeepSeek',
    'ZaiCoding',
    'BRAINS',
]