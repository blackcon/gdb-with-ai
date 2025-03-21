#!/bin/bash

# GDB-MCP 설치 및 설정 스크립트

echo "=== GDB-MCP 설치 및 설정 스크립트 ==="

# 필요한 패키지 설치 확인
echo "[1/5] 필요한 패키지 설치 중..."
pip install requests

# 디렉토리 설정
INSTALL_DIR="$HOME/.gdb-mcp"
mkdir -p "$INSTALL_DIR"

# 메인 파일 작성
echo "[2/5] GDB-MCP 스크립트 작성 중..."
cp gdb_mcp.py "$INSTALL_DIR/gdb_mcp.py"

# GDB 초기화 파일 설정
echo "[3/5] GDB 초기화 파일 설정 중..."
GDB_INIT="$HOME/.gdbinit"

# 기존 .gdbinit 파일 백업
if [ -f "$GDB_INIT" ]; then
    cp "$GDB_INIT" "$GDB_INIT.backup"
    echo ".gdbinit 파일을 백업했습니다: $GDB_INIT.backup"
fi

# .gdbinit에 GDB-MCP 로드 명령 추가
if grep -q "gdb_mcp.py" "$GDB_INIT" 2>/dev/null; then
    echo "GDB-MCP가 이미 .gdbinit에 설정되어 있습니다."
else
    echo "source $INSTALL_DIR/gdb_mcp.py" >> "$GDB_INIT"
    echo ".gdbinit에 GDB-MCP 로드 명령을 추가했습니다."
fi

# API 키 설정
echo "[4/5] Anthropic API 키 설정 중..."
read -p "Anthropic API 키를 입력하세요 (입력하지 않으면 나중에 mcp-setup 명령으로 설정 가능): " API_KEY

if [ -n "$API_KEY" ]; then
    echo "export ANTHROPIC_API_KEY=$API_KEY" >> "$HOME/.bashrc"
    echo "export ANTHROPIC_API_KEY=$API_KEY" >> "$HOME/.zshrc" 2>/dev/null
    echo "Anthropic API 키가 환경 변수에 설정되었습니다."
else
    echo "API 키를 설정하지 않았습니다. GDB 내에서 'mcp-setup API_KEY' 명령으로 설정할 수 있습니다."
fi

# 설치 완료
echo "[5/5] 설치 완료!"
echo ""
echo "GDB-MCP가 성공적으로 설치되었습니다!"
echo "GDB를 실행한 후 'mcp-help' 명령으로 사용 방법을 확인하세요."
echo ""
echo "새 터미널을 열거나 다음 명령어를 실행하여 환경 변수를 적용하세요:"
echo "  source ~/.bashrc  # Bash 쉘 사용 시"
echo "  source ~/.zshrc   # Zsh 쉘 사용 시"
