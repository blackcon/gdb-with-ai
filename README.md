# gdb-with-ai
## preview
### 1) 버그 수정 요청
- 버그 발생
    <img width="559" alt="image" src="https://github.com/user-attachments/assets/31a11ecd-a488-4c1e-9660-54753953dd72" />

- command: mcp-fix
    <img width="863" alt="image" src="https://github.com/user-attachments/assets/be0e83fb-8bb2-4b0e-b26f-8aa0ac6eb0ae" />

### 2) 자동 디버깅

<img width="753" alt="image" src="https://github.com/user-attachments/assets/c6802233-f712-4d1c-9e3d-a51a0b5dc7ae" />
<img width="749" alt="image" src="https://github.com/user-attachments/assets/a440a77e-fbc1-4c8d-9963-bbbb70e4ca5e" />


# GDB-MCP: GDB와 AI 모델 통합 시스템 가이드

이 가이드는 GDB(GNU Debugger)와 MCP(Model Context Protocol)를 연결하여 AI 모델과 통합하는 방법을 설명합니다.

일 줄 알았으나.. MCP와는 조금 결이 다릅니다. 그냥 GDB에 AI를 통합한것이라고 봐주세요 :)

## A. 개요

GDB-MCP는 디버깅 과정에서 AI의 도움을 받을 수 있도록 GDB를 확장한 시스템입니다. 

주요 기능:

- 현재 디버깅 컨텍스트를 기반으로 AI에게 질문하기
- 코드 및 함수에 대한 AI 설명 요청
- 버그 수정 제안 받기
- AI에게 자동으로 디버깅하도록 하기

## B. 사전 요구 사항

1. Anthropic API 키 (Claude 모델 사용) / 혹은 Gemini API 키
2. Python `requests` 라이브러리

## C. 설치 방법

### 1. 자동 설치 (권장)

1. 설치 스크립트를 다운로드하여 실행:

```bash
wget -O install-gdb-mcp.sh https://raw.githubusercontent.com/your-repo/gdb-mcp/main/install.sh
chmod +x install-gdb-mcp.sh
./install-gdb-mcp.sh
```

2. 프롬프트에 따라 Anthropic API 키를 입력하거나 나중에 설정할 수 있습니다.

### 2. 수동 설치

1. GDB-MCP 스크립트 저장:
   - `~/.gdb-mcp/` 디렉토리 생성
   - 첫 번째 코드 블록의 내용을 `~/.gdb-mcp/gdb_mcp.py`에 저장

2. GDB 초기화 파일 설정:
   - `~/.gdbinit` 파일에 다음 줄 추가: `source ~/.gdb-mcp/gdb_mcp.py`

3. Anthropic API 키 설정:
   - 환경 변수에 설정: `export ANTHROPIC_API_KEY=your_api_key`
   - 또는 GDB 내에서 `mcp-setup` 명령 사용

## D. 사용 방법

### 1. 기본 명령어

GDB 내에서 다음 명령어를 사용할 수 있습니다:

- `mcp-help`: 도움말 표시
- `mcp-setup API_KEY`: API 키 설정

### 2. AI 통합 명령어

- `mcp-ask 질문`: 현재 디버깅 컨텍스트에 대해 AI에게 질문
- `mcp-explain [함수명]`: 현재 또는 지정된 함수에 대한 AI 설명 요청
- `mcp-fix`: 현재 발생한 버그에 대한 수정 제안 요청
- `mcp-agent 작업내용` : AI가 자동으로 GDB 명령어를 실행하며 분석 진행

### 3. 사용 예시

프로그램에서 세그먼트 오류가 발생한 경우:

```
(gdb) break main
(gdb) run
(gdb) continue  # 세그먼트 오류 발생
(gdb) mcp-ask "이 세그먼트 오류의 원인은 무엇인가요?"
```

함수 이해가 필요한 경우:

```
(gdb) list my_complex_function
(gdb) mcp-explain my_complex_function
```

버그 수정 제안이 필요한 경우:

```
(gdb) # 버그가 발생한 지점에서
(gdb) mcp-fix
```

프로그램 분석을 요청할 경우:

```
(gdb) mcp-agent "이 프로그램을 실행해보고 버그가 있다면 찾아줘"
```

## E. 작동 원리

1. **컨텍스트 수집**: GDB-MCP는 현재 디버깅 상태(스택 트레이스, 소스 코드, 변수 등)를 수집합니다.
2. **AI 쿼리 구성**: 수집된 정보를 기반으로 AI에게 보낼 쿼리를 구성합니다.
3. **AI 통신**: Anthropic API를 통해 Claude 모델에 쿼리를 전송합니다.
4. **응답 처리**: AI의 응답을 사용자에게 표시합니다.

## F. 확장 및 커스터마이징

### 1. 새 명령어 추가

새로운 GDB 명령어를 추가하려면:

1. `GDBCommand` 클래스를 상속하는 새 클래스 작성
2. `__init__`과 `invoke` 메서드 구현
3. `initialize()` 함수에서 인스턴스 생성

### 2. 컨텍스트 수집 확장

더 많은 디버깅 정보를 수집하려면:

1. `GDBContextExtractor` 클래스에 새 메서드 추가
2. 명령어 클래스의 `_collect_debug_context` 메서드 수정

### 3. 다른 AI 모델 사용

Claude 외의 다른 AI 모델을 사용하려면:

1. `MCPClient` 클래스를 수정하여 다른 API와 통신하도록 변경
2. 프롬프트 구성 방식을 해당 모델에 맞게 조정

## G. 문제 해결

### 1. 일반적인 문제

- **API 연결 오류**: 인터넷 연결과 API 키가 올바른지 확인
- **GDB 로딩 오류**: GDB 버전 확인 및 Python 지원 확인
- **명령어 인식 실패**: `.gdbinit` 파일이 올바르게 구성되었는지 확인

### 2. 로그 및 디버깅

문제 해결을 위해 로깅을 활성화:

```python
import logging
logging.basicConfig(filename='~/.gdb-mcp/debug.log', level=logging.DEBUG)
```

## H. 주의사항

1. 민감한 코드를 외부 AI 서비스에 전송하므로 보안 정책을 확인하세요.
2. AI 응답은 항상 검증이 필요합니다. 제안된 수정 사항은 주의해서 적용하세요.
3. API 호출에는 비용이 발생할 수 있습니다. 사용량을 모니터링하세요.

## I. 결론

GDB-MCP를 사용하면 디버깅 과정에서 AI의 도움을 쉽게 받을 수 있습니다. 코드 이해, 버그 분석, 해결책 제안 등의 작업을 더 효율적으로 수행할 수 있습니다.

질문이나 더 자세한 정보가 필요하시면 알려주세요!
