#!/bin/bash

cat <<'EOF'
 █████╗ ██╗      ███████╗ ██████╗ ███████╗ █████╗ ██████╗
██╔══██╗██║      ██╔════╝██╔══██╗██╔════╝██╔══██╗██╔══██╗
███████║██║      █████╗  ██████╔╝█████╗  ███████║██║  ██║
██╔══██║██║      ██╔══╝  ██╔══██╗██╔══╝  ██╔══██║██║  ██║
██║  ██║███████╗ ██║     ██║  ██║███████╗██║  ██║██████╔╝
╚═╝  ╚═╝╚══════╝ ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝
EOF

# Inicia o MCP server em background
uv run alfread &
MCP_PID=$!
echo "MCP server iniciado (PID $MCP_PID)"

# Inicia o Playwright MCP em background (navegador persistente)
npx @playwright/mcp@latest --port 3100 &
PW_PID=$!
echo "Playwright MCP iniciado (PID $PW_PID)"

# Aguarda os servidores subirem
sleep 3

# Inicia o agente de voz
echo "Iniciando agente de voz..."
uv run alfread_voice

# Ao encerrar o agente, mata os servidores
kill $MCP_PID $PW_PID
