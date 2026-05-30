"""Tests for Nanocode v1.1 (Chapter 12 - The Capstone)."""

import os
import json
import threading
import tempfile
import pytest
from http.server import HTTPServer, BaseHTTPRequestHandler

from nanocode import (
    Agent, AgentStop, Thought, ToolCall, Memory, ToolContext,
    ReadFile, WriteFile, WritePlan, ListFiles, SearchCodebase, SaveMemory, RunCommand, SearchWeb,
    BRAINS, tools, get_tool, tool_definitions, M365
)


# --- Fake Brain for Testing ---

class FakeBrain:
    """Fake brain for testing - returns predictable responses."""
    context_limit = 200_000
    last_input_tokens = 0

    def __init__(self, responses=None, memory=None, tools=None):
        self.memory = memory
        self.tools = tools or []
        self.responses = responses or [Thought(text="Fake response", raw_content=[{"type": "text", "text": "Fake response"}])]
        self.call_count = 0
        self.last_conversation = None

    def think(self, conversation):
        self.last_conversation = list(conversation)
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return Thought(text="No more responses", raw_content=[{"type": "text", "text": "No more responses"}])


# --- Chapter 11: SearchWeb Tool Tests ---

def test_search_web_tool_exists():
    """Verify SearchWeb class exists with required attributes."""
    tool = SearchWeb()
    assert tool.name == "search_web"
    assert tool.description is not None
    assert tool.input_schema is not None
    assert "query" in tool.input_schema["properties"]


def test_search_web_in_tools_list():
    """Verify SearchWeb is registered in the tools list."""
    tool_names = [t.name for t in tools]
    assert "search_web" in tool_names


def test_search_web_can_be_found():
    """Verify get_tool can find search_web."""
    tool = get_tool(tools, "search_web")
    assert tool is not None
    assert tool.name == "search_web"


def test_search_web_in_tool_definitions():
    """Verify search_web appears in tool definitions for API."""
    definitions = tool_definitions(tools)
    names = [d["name"] for d in definitions]
    assert "search_web" in names


def test_search_web_execute_success(monkeypatch):
    """Verify SearchWeb.execute() returns formatted results."""
    fake_results = [
        {"title": "Python 3.13", "href": "https://python.org", "body": "Latest release"},
    ]
    monkeypatch.setattr("nanocode.DDGS", lambda: type("FakeDDGS", (), {"text": lambda self, q, max_results=3: fake_results})())
    tool = SearchWeb()
    context = ToolContext()
    result = tool.execute(context, "latest python version")
    assert "Python 3.13" in result
    assert "https://python.org" in result


def test_search_web_execute_no_results(monkeypatch):
    """Verify SearchWeb.execute() handles empty results."""
    monkeypatch.setattr("nanocode.DDGS", lambda: type("FakeDDGS", (), {"text": lambda self, q, max_results=3: []})())
    tool = SearchWeb()
    context = ToolContext()
    result = tool.execute(context, "impossible query xyz")
    assert "No results found" in result


def test_search_web_execute_error(monkeypatch):
    """Verify SearchWeb.execute() handles errors gracefully."""
    def raise_error():
        raise RuntimeError("Network down")
    monkeypatch.setattr("nanocode.DDGS", lambda: type("FakeDDGS", (), {"text": lambda self, q, max_results=3: raise_error()})())
    tool = SearchWeb()
    context = ToolContext()
    result = tool.execute(context, "test query")
    assert "Error" in result


# --- Previous Chapter Tests (Cumulative) ---

def test_handle_input_returns_string():
    """Basic test: handle_input returns a string."""
    agent = Agent(brain=FakeBrain(), tools=tools)
    result = agent.handle_input("Hello")
    assert isinstance(result, str)


def test_quit_command_raises_agent_stop():
    """Verify /q raises AgentStop."""
    agent = Agent(brain=FakeBrain(), tools=tools)
    try:
        agent.handle_input("/q")
        assert False, "Should have raised AgentStop"
    except AgentStop:
        pass


def test_messages_accumulate():
    """Verify conversation history accumulates."""
    agent = Agent(brain=FakeBrain(), tools=tools)
    agent.handle_input("First message")
    agent.handle_input("Second message")
    # Should have 4 messages: user, assistant, user, assistant
    assert len(agent.conversation) == 4


def test_brains_registry_has_expected_providers():
    """Verify BRAINS registry contains all providers."""
    assert "claude" in BRAINS
    assert "deepseek" in BRAINS
    assert "ollama" in BRAINS


def test_read_file_adds_line_numbers():
    """Verify ReadFile prefixes each line with line numbers."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("line one\nline two\nline three\n")
        temp_path = f.name

    try:
        tool = ReadFile()
        context = ToolContext()
        result = tool.execute(context, temp_path)
        assert "1 | line one" in result
        assert "2 | line two" in result
        assert "3 | line three" in result
    finally:
        os.unlink(temp_path)


def test_write_file_creates_file():
    """Verify WriteFile creates a file with content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.txt")
        tool = WriteFile()
        context = ToolContext()
        result = tool.execute(context, path, "hello world")

        assert os.path.exists(path)
        assert "Successfully wrote" in result
        with open(path) as f:
            assert f.read() == "hello world"


def test_plan_mode_hides_write_tools():
    """Verify plan mode removes write tools from brain's menu."""
    agent = Agent(brain=FakeBrain(), tools=tools, mode="plan")
    tool_names = [t["name"] for t in agent.brain.tools]
    assert "write_file" not in tool_names
    assert "edit_file" not in tool_names
    assert "run_command" not in tool_names
    assert "write_plan" in tool_names
    assert "read_file" in tool_names
    assert "search_web" in tool_names


def test_act_mode_shows_all_tools():
    """Verify act mode includes all tools in brain's menu."""
    agent = Agent(brain=FakeBrain(), tools=tools, mode="act")
    tool_names = [t["name"] for t in agent.brain.tools]
    assert "write_file" in tool_names
    assert "edit_file" in tool_names
    assert "run_command" in tool_names


def test_mode_switch_updates_brain_tools():
    """Verify switching mode updates the brain's tool menu."""
    agent = Agent(brain=FakeBrain(), tools=tools, mode="plan")
    plan_names = [t["name"] for t in agent.brain.tools]
    assert "write_file" not in plan_names
    agent.handle_input("/mode act")
    act_names = [t["name"] for t in agent.brain.tools]
    assert "write_file" in act_names


def test_write_plan_saves_file():
    """Verify WritePlan creates PLAN.md with content."""
    original_dir = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            tool = WritePlan()
            context = ToolContext()
            result = tool.execute(context, content="# My Plan")
            assert "Plan saved" in result
        finally:
            os.chdir(original_dir)


def test_write_file_writes_file():
    """Verify WriteFile creates a file with content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test.py")
        tool = WriteFile()
        context = ToolContext()
        result = tool.execute(context, file_path, "print('hello')")
        assert "Successfully wrote" in result


def test_run_command_executes():
    """Verify RunCommand works."""
    tool = RunCommand()
    context = ToolContext()
    result = tool.execute(context, "echo hello")
    assert "hello" in result


def test_ollama_in_brains_registry():
    """Verify Ollama is in the BRAINS registry."""
    assert "ollama" in BRAINS


def test_version_is_1_1():
    """Verify version number is 1.1 in main()."""
    import nanocode
    import inspect
    source = inspect.getsource(nanocode.main)
    assert "v1.1" in source


# --- Context Compaction Tests ---

def test_compact_conversation_summarizes():
    """Verify compaction replaces conversation with summary."""
    summary = Thought(
        text="Summary of conversation",
        raw_content=[{"type": "text", "text": "Summary of conversation"}]
    )
    responses = [
        Thought(text="Response 1", raw_content=[{"type": "text", "text": "Response 1"}]),
        summary,
    ]
    brain = FakeBrain(responses=responses)
    brain.last_input_tokens = 200_000  # Over 75% threshold
    agent = Agent(brain=brain, tools=tools, mode="act")

    agent.handle_input("Do something")

    # After compaction, conversation should be short (summary + current response)
    assert len(agent.conversation) <= 4
    assert "Summary" in str(agent.conversation[0]["content"])


# --- M365 Brain Tests ---


class FakeM365Server:
    """Tiny HTTP server that mimics the Puppeteer server v2 Anthropic API."""

    def __init__(self, port=13000):
        self.port = port
        self.responses = []
        self.requests_received = []
        self._server = None

    def start(self):
        """Start in background thread."""
        server_ref = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self._json(200, {"status": "ok", "session": {"ready": True}})
                elif self.path == '/v1/models':
                    self._json(200, {"object": "list", "data": [{"id": "m365-copilot"}]})
                else:
                    self._json(404, {"error": "not found"})

            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length))
                server_ref.requests_received.append(body)

                default_resp = {
                    "id": "msg_test",
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Hello from M365"}],
                    "model": "m365-copilot",
                    "stop_reason": "end_turn",
                    "stop_sequence": None,
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                }
                resp = server_ref.responses.pop(0) if server_ref.responses else default_resp
                self._json(200, resp)

            def _json(self, code, data):
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())

            def log_message(self, *args):
                pass

        class ReusableHTTPServer(HTTPServer):
            allow_reuse_address = True

        self._server = ReusableHTTPServer(('127.0.0.1', self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()


def test_m365_in_brains_registry():
    """Verify M365 is in the BRAINS registry."""
    assert "m365" in BRAINS


def test_m365_health_check_fails_when_server_down():
    """Verify M365 raises ValueError when server unreachable."""
    original_url = os.environ.get("M365_BASE_URL")
    os.environ["M365_BASE_URL"] = "http://127.0.0.1:19999"
    try:
        with pytest.raises(ValueError, match="Cannot connect"):
            M365()
    finally:
        if original_url is None:
            os.environ.pop("M365_BASE_URL", None)
        else:
            os.environ["M365_BASE_URL"] = original_url


def test_m365_text_response():
    """Verify M365 brain parses text response correctly."""
    server = FakeM365Server()
    server.start()
    try:
        brain = M365.__new__(M365)  # Skip __init__ health check
        brain.base_url = f"http://127.0.0.1:{server.port}"
        brain.url = f"{brain.base_url}/v1/messages"
        brain.tools = []
        brain.system = None
        brain.model = "m365-copilot"
        brain.memory = None
        brain.timeout = 10
        brain._system_sent = False

        thought = brain.think([{"role": "user", "content": "Hello"}])
        assert thought.text == "Hello from M365"
        assert thought.tool_calls == []
    finally:
        server.stop()


def test_m365_tool_call_response():
    """Verify M365 brain parses tool_use response correctly."""
    server = FakeM365Server(port=13001)
    server.responses.append({
        "id": "msg_tool",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Let me read that file."},
            {"type": "tool_use", "id": "toolu_123", "name": "read_file",
             "input": {"path": "/tmp/test.py"}},
        ],
        "model": "m365-copilot",
        "stop_reason": "tool_use",
        "stop_sequence": None,
        "usage": {"input_tokens": 100, "output_tokens": 50},
    })
    server.start()
    try:
        brain = M365.__new__(M365)
        brain.base_url = f"http://127.0.0.1:{server.port}"
        brain.url = f"{brain.base_url}/v1/messages"
        brain.tools = []
        brain.system = None
        brain.model = "m365-copilot"
        brain.memory = None
        brain.timeout = 10
        brain._system_sent = False

        thought = brain.think([{"role": "user", "content": "Read /tmp/test.py"}])
        assert thought.text == "Let me read that file."
        assert len(thought.tool_calls) == 1
        assert thought.tool_calls[0].name == "read_file"
        assert thought.tool_calls[0].args == {"path": "/tmp/test.py"}
    finally:
        server.stop()


def test_m365_sends_system_and_tools_on_first_call_only():
    """Verify system prompt and tools sent on first think(), omitted on subsequent calls."""
    server = FakeM365Server(port=13004)
    server.start()
    try:
        brain = M365.__new__(M365)
        brain.base_url = f"http://127.0.0.1:{server.port}"
        brain.url = f"{brain.base_url}/v1/messages"
        brain.system = "You are a coding agent."
        brain.tools = [{
            "name": "read_file",
            "description": "Read a file",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }]
        brain.model = "m365-copilot"
        brain.memory = None
        brain.timeout = 10
        brain._system_sent = False

        # First call — system and tools should be present
        brain.think([{"role": "user", "content": "Hello"}])
        req1 = server.requests_received[0]
        assert req1["system"] == "You are a coding agent."
        assert len(req1["tools"]) == 1
        assert req1["tools"][0]["name"] == "read_file"

        # Second call — system and tools should NOT be present
        brain.think([{"role": "user", "content": "Hello again"}])
        req2 = server.requests_received[1]
        assert "system" not in req2, f"System prompt should not be sent on second call, got: {req2.get('system')}"
        assert "tools" not in req2, f"Tools should not be sent on second call, got: {req2.get('tools')}"
    finally:
        server.stop()


def test_m365_multi_tool_calls():
    """Verify M365 brain parses multiple tool_use blocks correctly."""
    server = FakeM365Server(port=13002)
    server.responses.append({
        "id": "msg_multi",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "tool_use", "id": "toolu_1", "name": "read_file",
             "input": {"path": "a.py"}},
            {"type": "tool_use", "id": "toolu_2", "name": "read_file",
             "input": {"path": "b.py"}},
        ],
        "model": "m365-copilot",
        "stop_reason": "tool_use",
        "stop_sequence": None,
        "usage": {"input_tokens": 100, "output_tokens": 50},
    })
    server.start()
    try:
        brain = M365.__new__(M365)
        brain.base_url = f"http://127.0.0.1:{server.port}"
        brain.url = f"{brain.base_url}/v1/messages"
        brain.tools = []
        brain.system = None
        brain.model = "m365-copilot"
        brain.memory = None
        brain.timeout = 10

        brain._system_sent = False
        thought = brain.think([{"role": "user", "content": "Read both files"}])
        assert len(thought.tool_calls) == 2
        assert thought.tool_calls[0].args == {"path": "a.py"}
        assert thought.tool_calls[1].args == {"path": "b.py"}
    finally:
        server.stop()


def test_m365_with_agent_tool_loop():
    """Full integration: M365 brain + agent executes tool call and sends result back."""
    server = FakeM365Server(port=13003)
    # First call: M365 asks to read a file
    server.responses.append({
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Reading the file..."},
            {"type": "tool_use", "id": "toolu_r", "name": "read_file",
             "input": {"path": ".nanocode/memory.md"}},
        ],
        "model": "m365-copilot",
        "stop_reason": "tool_use",
        "stop_sequence": None,
        "usage": {"input_tokens": 100, "output_tokens": 50},
    })
    # Second call: M365 gives final answer after seeing tool result
    server.responses.append({
        "id": "msg_2",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "The memory file says: Nanocode"}],
        "model": "m365-copilot",
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 100, "output_tokens": 50},
    })
    server.start()
    try:
        brain = M365.__new__(M365)
        brain.base_url = f"http://127.0.0.1:{server.port}"
        brain.url = f"{brain.base_url}/v1/messages"
        brain.tools = tool_definitions(tools)
        brain.system = None
        brain.model = "m365-copilot"
        brain.memory = None
        brain.timeout = 10
        brain.context_limit = 200_000
        brain._system_sent = False
        brain.last_input_tokens = 0

        agent = Agent(brain=brain, tools=tools, mode="act", brain_name="m365")
        output = agent.handle_input("What does the memory file say?")

        assert "Nanocode" in output
        assert len(server.requests_received) == 2
        # Second request should contain the tool_result
        second_req = server.requests_received[1]
        assert second_req["messages"][-1]["role"] == "user"
        last_content = second_req["messages"][-1]["content"]
        if isinstance(last_content, list):
            assert any(b.get("type") == "tool_result" for b in last_content)
    finally:
        server.stop()
