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


class Claude(Brain):
    """Claude API implementation."""

    def __init__(self):
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
            "thinking": {
                "type": "enabled",
                "budget_tokens": 10000
            },
            "messages": conversation
        }

        response = request_with_retry(self.url, headers, payload)
        return self._parse_response(response.json()["content"])


class DeepSeek(Brain):
    """DeepSeek API (Anthropic-compatible)."""

    def __init__(self):
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

        response = request_with_retry(self.url, headers, payload)
        return self._parse_response(response.json()["content"])


class ZaiCoding(Brain):
    """Z.ai Coding Plan API implementation - Anthropic compatible."""

    def __init__(self):
        self.api_key = os.getenv("ZAI_CODING_API_KEY")
        if not self.api_key:
            raise ValueError("ZAI_CODING_API_KEY not found in .env")
        
        # Based on successful requests in logs, use the Anthropic-compatible endpoint
        # The logs show successful requests to: https://api.z.ai/api/anthropic/v1/messages
        base_url = os.getenv("ZAI_CODING_BASE_URL", "https://api.z.ai")
        endpoint_path = os.getenv("ZAI_CODING_PATH", "/api/anthropic/v1/messages")
        self.url = base_url + endpoint_path
        
        # Z.ai coding plan uses GLM models
        self.model = os.getenv("ZAI_CODING_MODEL", "GLM-4.7")
        
        print(f"🤖 Z.ai Coding Plan initialized:")
        print(f"   Model: {self.model}")
        print(f"   URL: {self.url}")

    def think(self, conversation):
        # Z.ai Coding Plan uses Anthropic-compatible headers
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

        response = request_with_retry(self.url, headers, payload)
        return self._parse_zai_response(response.json())

    def _parse_zai_response(self, response_data):
        """Convert z.ai API response format to Thought."""
        text_parts = []
        tool_calls = []
        thinking = None

        # Handle different response formats from z.ai
        if "content" in response_data:
            content = response_data["content"]
        elif "choices" in response_data:
            # OpenAI-style format
            choice = response_data["choices"][0]
            if "message" in choice:
                content = choice["message"].get("content", "")
                if isinstance(content, str):
                    return Thought(text=content)
            return Thought(text=str(response_data))
        else:
            # Fallback: try to extract any text
            return Thought(text=str(response_data))

        # Process content blocks
        if isinstance(content, str):
            return Thought(text=content)
        
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                    
                block_type = block.get("type")
                
                if block_type == "thinking":
                    thinking = block.get("thinking")
                elif block_type == "text":
                    text_parts.append(block.get("text", ""))
                elif block_type == "tool_use":
                    tool_calls.append(ToolCall(
                        id=block.get("id", ""),
                        name=block.get("name", ""),
                        args=block.get("input", {})
                    ))
                elif block_type == "tool_result":
                    # Handle tool results if they appear in responses
                    text_parts.append(f"Tool result: {block.get('content', '')}")

        return Thought(
            text="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
            thinking=thinking
        )


# Available brains
BRAINS = {
    "claude": Claude,
    "deepseek": DeepSeek,
    "zai": ZaiCoding,
}


# --- Agent Class ---

class Agent:
    """A coding agent with switchable brain."""

    def __init__(self, brain, brain_name="claude"):
        self.brain = brain
        self.brain_name = brain_name
        self.conversation = []

    def handle_input(self, user_input):
        """Handle user input. Returns output string, raises AgentStop to quit."""
        if user_input.strip() == "/q":
            raise AgentStop()

        if user_input.strip() == "/switch":
            return self._switch_brain()

        if not user_input.strip():
            return ""

        self.conversation.append({"role": "user", "content": user_input})

        try:
            thought = self.brain.think(self.conversation)
            if thought.thinking:
                lines = thought.thinking.strip().split("\n")[:5]
                for i, line in enumerate(lines):
                    prefix = "  💭 " if i == 0 else "     "
                    print(f"\033[2m{prefix}{line}\033[0m")
            text = thought.text or ""
            self.conversation.append({"role": "assistant", "content": text})
            return text
        except Exception as e:
            self.conversation.pop()
            return f"Error: {e}"

    def _switch_brain(self):
        """Toggle to the next brain."""
        names = list(BRAINS.keys())
        idx = names.index(self.brain_name)
        new_name = names[(idx + 1) % len(names)]

        try:
            self.brain = BRAINS[new_name]()
            self.brain_name = new_name
            return f"Switched to: {new_name}"
        except ValueError as e:
            return f"Cannot switch to {new_name}: {e}"


# --- Main Loop ---

def main():
    brain_name = os.getenv("NANOCODE_BRAIN", "claude")
    brain = BRAINS[brain_name]()
    agent = Agent(brain, brain_name)

    print(f"⚡ Nanocode v0.4 - Z.ai Edition (Direct API)")
    print(f"Commands: /q quit, /switch toggle brain")
    print(f"Brain: {brain_name}\n")

    while True:
        try:
            user_input = input(f"[{agent.brain_name}] ❯ ")
            output = agent.handle_input(user_input)
            if output:
                print(f"\n{output}\n")

        except (AgentStop, KeyboardInterrupt):
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()
