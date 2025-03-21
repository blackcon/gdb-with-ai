"""
GDB-MCP: GDB와 Model Context Protocol 통합 라이브러리
AI 에이전트 기능 추가
"""
import gdb
import json
import requests
import os
import re
import threading
import queue
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

class MCPClient:
    """Model Context Protocol 클라이언트 - Gemini 버전"""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro", api_url: str = "https://generativelanguage.googleapis.com/v1beta/models"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = api_url
        self.api_url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.messages = []

    def add_message(self, role: str, content: str):
        """대화 기록에 메시지 추가"""
        # Gemini API의 role은 'user' 또는 'model'을 사용합니다
        gemini_role = "model" if role == "assistant" else "user"
        self.messages.append({"role": gemini_role, "parts": [{"text": content}]})

    def query(self, message: str) -> str:
        """AI 모델에 쿼리 보내기"""
        self.add_message("user", message)

        # Gemini API는 contents라는 키를 사용하며 generationConfig를 별도로 설정합니다
        data = {
            "contents": self.messages,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4000,
                "topP": 0.95,
                "topK": 40
            }
        }

        response = requests.post(self.api_url, headers=self.headers, json=data)
        if response.status_code != 200:
            raise Exception(f"API 오류: {response.status_code} - {response.text}")

        result = response.json()

        # Gemini API 응답 구조에 따라 결과 추출
        try:
            response_content = result["candidates"][0]["content"]["parts"][0]["text"]
            self.add_message("assistant", response_content)
            return response_content
        except (KeyError, IndexError) as e:
            raise Exception(f"API 응답 파싱 오류: {str(e)} - {result}")

class GDBContextExtractor:
    """GDB에서 디버깅 컨텍스트 추출"""

    @staticmethod
    def get_backtrace() -> str:
        """스택 트레이스 추출"""
        try:
            result = gdb.execute("backtrace", to_string=True)
            return result
        except gdb.error as e:
            return f"스택 트레이스를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_current_source() -> str:
        """현재 소스 코드 추출"""
        try:
            result = gdb.execute("list", to_string=True)
            return result
        except gdb.error as e:
            return f"소스 코드를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_local_vars() -> str:
        """로컬 변수 추출"""
        try:
            result = gdb.execute("info locals", to_string=True)
            return result
        except gdb.error as e:
            return f"로컬 변수를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_threads() -> str:
        """스레드 정보 추출"""
        try:
            result = gdb.execute("info threads", to_string=True)
            return result
        except gdb.error as e:
            return f"스레드 정보를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_breakpoints() -> str:
        """브레이크포인트 정보 추출"""
        try:
            result = gdb.execute("info breakpoints", to_string=True)
            return result
        except gdb.error as e:
            return f"브레이크포인트 정보를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_register_values() -> str:
        """레지스터 값 추출"""
        try:
            result = gdb.execute("info registers", to_string=True)
            return result
        except gdb.error as e:
            return f"레지스터 값을 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_disassembly() -> str:
        """현재 함수 디스어셈블"""
        try:
            result = gdb.execute("disassemble", to_string=True)
            return result
        except gdb.error as e:
            return f"디스어셈블 결과를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def extract_error_info() -> str:
        """오류 정보 추출"""
        try:
            result = gdb.execute("print $_exception", to_string=True)
            return result
        except gdb.error as e:
            return f"오류 정보를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_file_info() -> str:
        """파일 정보 추출"""
        try:
            result = gdb.execute("info files", to_string=True)
            return result
        except gdb.error as e:
            return f"파일 정보를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_function_info() -> str:
        """함수 정보 추출"""
        try:
            result = gdb.execute("info functions", to_string=True)
            # 너무 길면 자르기
            if len(result) > 2000:
                result = result[:2000] + "...(이하 생략)..."
            return result
        except gdb.error as e:
            return f"함수 정보를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_sections_info() -> str:
        """섹션 정보 추출"""
        try:
            result = gdb.execute("maintenance info sections", to_string=True)
            return result
        except gdb.error as e:
            return f"섹션 정보를 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def get_program_status() -> str:
        """프로그램 상태 확인"""
        try:
            frame = gdb.selected_frame()
            return "프로그램이 실행 중입니다."
        except gdb.error:
            return "프로그램이 실행 중이 아닙니다."

    @staticmethod
    def get_memory(address: str, size: int = 16) -> str:
        """메모리 내용 추출"""
        try:
            result = gdb.execute(f"x/{size}xb {address}", to_string=True)
            return result
        except gdb.error as e:
            return f"메모리 내용을 가져올 수 없습니다: {str(e)}"

    @staticmethod
    def check_program_running() -> bool:
        """프로그램 실행 중인지 확인"""
        try:
            frame = gdb.selected_frame()
            return True
        except gdb.error:
            return False

class GDBCommand(gdb.Command):
    """GDB 커맨드 기본 클래스"""

    def __init__(self, command_name: str, command_class: int):
        super(GDBCommand, self).__init__(command_name, command_class)

class GDBCommandExecutor:
    """GDB 명령어 실행 관리자"""

    @staticmethod
    def execute_command(command: str) -> str:
        """GDB 명령어 실행 및 결과 반환"""
        try:
            result = gdb.execute(command, to_string=True)
            return result
        except gdb.error as e:
            return f"명령어 실행 오류: {str(e)}"

    @staticmethod
    def is_safe_command(command: str) -> bool:
        """안전한 명령어인지 확인"""
        # 프로그램을 종료시키거나 수정하는 명령어 금지
        unsafe_commands = [
            "quit", "exit", "detach", "kill", "set", "shell", "source",
            "define", "document", "handle", "signal", "attach"
        ]

        command_parts = command.strip().split()
        if not command_parts:
            return False

        cmd = command_parts[0].lower()
        return cmd not in unsafe_commands

class AIAgentCommand(GDBCommand):
    """AI 에이전트 GDB 명령어"""

    def __init__(self, mcp_client: MCPClient):
        super(AIAgentCommand, self).__init__("mcp-agent", gdb.COMMAND_USER)
        self.mcp_client = mcp_client
        self.context_extractor = GDBContextExtractor()
        self.command_executor = GDBCommandExecutor()
        self.max_iterations = 10  # 최대 반복 횟수
        print("MCP-AGENT 커맨드가 등록되었습니다. 'mcp-agent 질문내용'으로 사용하세요.")

    def invoke(self, arg: str, from_tty: bool):
        """커맨드 실행"""
        if not arg:
            print("사용법: mcp-agent 작업내용/질문")
            return

        print("\n=== AI 에이전트 시작 ===")
        print(f"작업: {arg}")
        print("초기 컨텍스트 수집 중...")

        # 프로그램 실행 상태 확인
        program_running = self.context_extractor.check_program_running()

        # 초기 컨텍스트 수집
        if program_running:
            context = self._collect_debug_context()
        else:
            context = self._collect_limited_context()

        # AI 에이전트 초기화 메시지
        system_message = """당신은 GDB 디버거 내에서 동작하는 AI 디버깅 에이전트입니다.
사용자의 요청에 따라 GDB 명령어를 자동으로 실행하고 결과를 분석할 수 있습니다.

GDB 명령어를 실행하려면 다음 형식으로 응답하세요:
```gdb-command
명령어1
명령어2
...
```

분석과 결과를 제공할 때는 다음 형식으로 응답하세요:
```analysis
분석 내용과 설명
```

다음 단계로 진행하려면:
```next-step
다음 단계 설명
```

분석 완료시:
```complete
최종 결론과 분석 결과
```

주의사항:
1. 안전하지 않은 명령어(quit, exit, kill 등)는 실행되지 않습니다.
2. 한 번에 너무 많은 명령어를 실행하지 마세요.
3. 분석 결과는 간결하고 명확하게 작성하세요.
4. 작업을 완료하면 반드시 ```complete```로 끝내세요.
"""

        # 사용자 작업 요청
        user_request = f"""다음 작업을 수행해주세요: {arg}

현재 디버깅 컨텍스트:
{context}

단계별로 분석하고 필요한 GDB 명령어를 실행하여 요청을 해결해주세요."""

        # AI 에이전트 초기화
        self.mcp_client.messages = []  # 메시지 초기화
        self.mcp_client.add_message("user", system_message)
        self.mcp_client.add_message("assistant", "디버깅 에이전트 초기화 완료. 요청을 분석하겠습니다.")

        # 에이전트 실행
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- 단계 {iteration}/{self.max_iterations} ---")

            if iteration == 1:
                # 첫 번째 반복에서는 사용자 요청 전달
                response = self.mcp_client.query(user_request)
            else:
                # 이후 반복에서는 이전 결과에 이어서 진행
                response = self.mcp_client.messages[-1]["parts"][0]["text"]

            # 응답 파싱 및 처리
            if self._process_agent_response(response):
                # 완료 신호가 있으면 종료
                break

            # 최대 반복 횟수 도달 확인
            if iteration >= self.max_iterations:
                print("\n최대 반복 횟수에 도달했습니다. 작업이 완료되지 않았을 수 있습니다.")

        print("\n=== AI 에이전트 완료 ===")

    def _process_agent_response(self, response: str) -> bool:
        """AI 에이전트 응답 처리"""
        # 명령어 블록 찾기
        command_match = re.search(r'```gdb-command\n(.*?)```', response, re.DOTALL)
        if command_match:
            commands = command_match.group(1).strip().split('\n')
            print("\n[AI 에이전트가 명령어 실행 중...]")
            results = []

            for cmd in commands:
                cmd = cmd.strip()
                if not cmd:
                    continue

                print(f"실행: {cmd}")
                if self.command_executor.is_safe_command(cmd):
                    result = self.command_executor.execute_command(cmd)
                    print(result)
                    results.append(f"명령어: {cmd}\n결과:\n{result}")
                else:
                    msg = f"안전하지 않은 명령어입니다: {cmd}"
                    print(msg)
                    results.append(msg)

            # 결과를 AI에게 전달
            results_text = "\n\n".join(results)
            self.mcp_client.query(f"명령어 실행 결과:\n\n{results_text}")

        # 분석 블록 찾기
        analysis_match = re.search(r'```analysis\n(.*?)```', response, re.DOTALL)
        if analysis_match:
            analysis = analysis_match.group(1).strip()
            print("\n[AI 분석 결과]")
            print(analysis)

        # 다음 단계 블록 찾기
        next_step_match = re.search(r'```next-step\n(.*?)```', response, re.DOTALL)
        if next_step_match:
            next_step = next_step_match.group(1).strip()
            print("\n[다음 단계]")
            print(next_step)

        # 완료 블록 찾기
        complete_match = re.search(r'```complete\n(.*?)```', response, re.DOTALL)
        if complete_match:
            conclusion = complete_match.group(1).strip()
            print("\n[최종 결론]")
            print(conclusion)
            return True  # 완료 신호

        return False  # 계속 진행

    def _collect_debug_context(self) -> str:
        """디버깅 컨텍스트 수집"""
        context_parts = [
            ("프로그램 상태:", self.context_extractor.get_program_status()),
            ("스택 트레이스:", self.context_extractor.get_backtrace()),
            ("현재 소스 코드:", self.context_extractor.get_current_source()),
            ("로컬 변수:", self.context_extractor.get_local_vars()),
            ("스레드 정보:", self.context_extractor.get_threads()),
            ("브레이크포인트:", self.context_extractor.get_breakpoints()),
            ("오류 정보:", self.context_extractor.extract_error_info())
        ]

        context = "\n\n".join([f"=== {title} ===\n{content}" for title, content in context_parts if content])
        return context

    def _collect_limited_context(self) -> str:
        """프로그램이 실행 중이 아닐 때 제한된 컨텍스트 수집"""
        context_parts = [
            ("프로그램 상태:", self.context_extractor.get_program_status()),
            ("파일 정보:", self.context_extractor.get_file_info()),
            ("함수 정보:", self.context_extractor.get_function_info()),
            ("섹션 정보:", self.context_extractor.get_sections_info())
        ]

        context = "\n\n".join([f"=== {title} ===\n{content}" for title, content in context_parts if content])
        return context

class MCPAskCommand(GDBCommand):
    """AI에게 질문하는 GDB 커맨드"""

    def __init__(self, mcp_client: MCPClient):
        super(MCPAskCommand, self).__init__("mcp-ask", gdb.COMMAND_USER)
        self.mcp_client = mcp_client
        self.context_extractor = GDBContextExtractor()
        print("MCP-ASK 커맨드가 등록되었습니다. 'mcp-ask 질문내용'으로 사용하세요.")

    def invoke(self, arg: str, from_tty: bool):
        """커맨드 실행"""
        if not arg:
            print("사용법: mcp-ask 질문내용")
            return

        # 프로그램 실행 상태 확인
        program_running = self.context_extractor.check_program_running()

        if program_running:
            # 디버깅 컨텍스트 수집
            context = self._collect_debug_context()
        else:
            # 제한된 컨텍스트 수집
            context = self._collect_limited_context()
            print("경고: 프로그램이 실행 중이 아닙니다. 제한된 컨텍스트로 분석을 진행합니다.")

        # AI에 질문 보내기
        prompt = f"""현재 디버깅 중인 코드에 대한 질문이 있습니다: {arg}

현재 디버깅 컨텍스트:
{context}

위 정보를 바탕으로 질문에 답변해주세요."""

        print("AI에 질문 중입니다...")
        try:
            response = self.mcp_client.query(prompt)
            print("\n--- AI 응답 ---")
            print(response)
            print("---------------")
        except Exception as e:
            print(f"오류 발생: {str(e)}")

    def _collect_debug_context(self) -> str:
        """디버깅 컨텍스트 수집"""
        context_parts = [
            ("스택 트레이스:", self.context_extractor.get_backtrace()),
            ("현재 소스 코드:", self.context_extractor.get_current_source()),
            ("로컬 변수:", self.context_extractor.get_local_vars()),
            ("스레드 정보:", self.context_extractor.get_threads()),
            ("브레이크포인트:", self.context_extractor.get_breakpoints()),
            ("오류 정보:", self.context_extractor.extract_error_info())
        ]

        context = "\n\n".join([f"=== {title} ===\n{content}" for title, content in context_parts if content])
        return context

    def _collect_limited_context(self) -> str:
        """프로그램이 실행 중이 아닐 때 제한된 컨텍스트 수집"""
        context_parts = [
            ("파일 정보:", self.context_extractor.get_file_info()),
            ("함수 정보:", self.context_extractor.get_function_info()),
            ("섹션 정보:", self.context_extractor.get_sections_info())
        ]

        context = "\n\n".join([f"=== {title} ===\n{content}" for title, content in context_parts if content])
        return context

class MCPExplainCommand(GDBCommand):
    """현재 함수/코드를 설명해주는 GDB 커맨드"""

    def __init__(self, mcp_client: MCPClient):
        super(MCPExplainCommand, self).__init__("mcp-explain", gdb.COMMAND_USER)
        self.mcp_client = mcp_client
        self.context_extractor = GDBContextExtractor()
        print("MCP-EXPLAIN 커맨드가 등록되었습니다. 'mcp-explain [함수명]'으로 사용하세요.")

    def invoke(self, arg: str, from_tty: bool):
        """커맨드 실행"""
        # 함수 이름이 제공되면 해당 함수 검사, 아니면 현재 함수
        if arg:
            try:
                gdb.execute(f"list {arg}", to_string=True)
            except gdb.error:
                print(f"함수 '{arg}'를 찾을 수 없습니다.")
                return

        # 소스 코드 가져오기
        source_code = self.context_extractor.get_current_source()
        disassembly = self.context_extractor.get_disassembly()

        # AI에 설명 요청
        prompt = f"""다음 코드 및 어셈블리를 분석하고 설명해주세요:

=== 소스 코드 ===
{source_code}

=== 어셈블리 ===
{disassembly}

이 코드가 무엇을 하는지, 어떻게 작동하는지, 그리고 잠재적인 문제점이 있는지 설명해주세요."""

        print("AI에 분석 요청 중입니다...")
        try:
            response = self.mcp_client.query(prompt)
            print("\n--- AI 분석 ---")
            print(response)
            print("---------------")
        except Exception as e:
            print(f"오류 발생: {str(e)}")

class MCPFixCommand(GDBCommand):
    """버그 수정 제안을 위한 GDB 커맨드"""

    def __init__(self, mcp_client: MCPClient):
        super(MCPFixCommand, self).__init__("mcp-fix", gdb.COMMAND_USER)
        self.mcp_client = mcp_client
        self.context_extractor = GDBContextExtractor()
        print("MCP-FIX 커맨드가 등록되었습니다. 'mcp-fix'로 사용하세요.")

    def invoke(self, arg: str, from_tty: bool):
        """커맨드 실행"""
        # 디버깅 컨텍스트 수집
        context = self._collect_debug_context()

        # AI에 수정 제안 요청
        prompt = f"""현재 디버깅 중인 코드에서 발생한 문제를 해결하기 위한 수정 방법을 제안해주세요.

현재 디버깅 컨텍스트:
{context}

문제를 분석하고, 구체적인 수정 방법을 제안해주세요."""

        print("AI에 수정 제안 요청 중입니다...")
        try:
            response = self.mcp_client.query(prompt)
            print("\n--- AI 수정 제안 ---")
            print(response)
            print("---------------")
        except Exception as e:
            print(f"오류 발생: {str(e)}")

    def _collect_debug_context(self) -> str:
        """디버깅 컨텍스트 수집"""
        context_parts = [
            ("스택 트레이스:", self.context_extractor.get_backtrace()),
            ("현재 소스 코드:", self.context_extractor.get_current_source()),
            ("로컬 변수:", self.context_extractor.get_local_vars()),
            ("오류 정보:", self.context_extractor.extract_error_info()),
            ("레지스터 값:", self.context_extractor.get_register_values()),
            ("디스어셈블리:", self.context_extractor.get_disassembly())
        ]

        context = "\n\n".join([f"=== {title} ===\n{content}" for title, content in context_parts if content])
        return context

class GDBMCPManager:
    """GDB-MCP 통합 관리자"""

    def __init__(self, api_key: Optional[str] = None):
        """초기화"""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            print("경고: API 키가 설정되지 않았습니다. 'mcp-setup API_KEY'로 설정하세요.")
        else:
            self._initialize_mcp()

    def _initialize_mcp(self):
        """MCP 초기화"""
        self.mcp_client = MCPClient(self.api_key, model_name="gemini-1.5-flash-latest")
        self.commands = {
            "ask": MCPAskCommand(self.mcp_client),
            "explain": MCPExplainCommand(self.mcp_client),
            "fix": MCPFixCommand(self.mcp_client),
            "agent": AIAgentCommand(self.mcp_client)
        }
        print("GDB-MCP가 초기화되었습니다.")

class MCPSetupCommand(GDBCommand):
    """MCP 설정을 위한 GDB 커맨드"""

    def __init__(self, manager: GDBMCPManager):
        super(MCPSetupCommand, self).__init__("mcp-setup", gdb.COMMAND_USER)
        self.manager = manager
        print("MCP-SETUP 커맨드가 등록되었습니다. 'mcp-setup API_KEY'로 사용하세요.")

    def invoke(self, arg: str, from_tty: bool):
        """커맨드 실행"""
        if not arg:
            print("사용법: mcp-setup API_KEY")
            return

        self.manager.api_key = arg
        self.manager._initialize_mcp()
        print("API 키가 설정되었습니다.")

class MCPHelpCommand(GDBCommand):
    """MCP 도움말을 위한 GDB 커맨드"""

    def __init__(self):
        super(MCPHelpCommand, self).__init__("mcp-help", gdb.COMMAND_USER)
        print("MCP-HELP 커맨드가 등록되었습니다. 'mcp-help'로 사용하세요.")

    def invoke(self, arg: str, from_tty: bool):
        """커맨드 실행"""
        help_text = """
=== GDB-MCP 도움말 ===

기본 명령어:
  mcp-setup API_KEY   - API 키 설정
  mcp-help            - 이 도움말 표시

AI 통합 명령어:
  mcp-ask 질문        - 현재 디버깅 컨텍스트에 대해 AI에게 질문
  mcp-explain [함수명] - 현재 또는 지정된 함수에 대한 AI 설명 요청
  mcp-fix             - 현재 발생한 버그에 대한 수정 제안 요청
  mcp-agent 작업내용   - AI가 자동으로 GDB 명령어를 실행하며 분석 진행
"""
        print(help_text)

# 초기화 및 명령어 등록
def initialize():
    """GDB-MCP 초기화"""
    manager = GDBMCPManager()
    MCPSetupCommand(manager)
    MCPHelpCommand()
    print("GDB-MCP가 로드되었습니다. 'mcp-help'를 입력하여 도움말을 확인하세요.")

# GDB 시작 시 자동으로 실행
initialize()
