"""
Shell tools — executa comandos no terminal e usa o Claude Code.
"""

import subprocess


def register(mcp):

    @mcp.tool()
    def run_shell(command: str) -> str:
        """Executa um comando shell no computador do chefe."""
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        output = result.stdout or result.stderr or "Comando executado sem saída."
        return output[:4000]

    @mcp.tool()
    def claude_code(prompt: str, directory: str = "/home/barbozza") -> str:
        """Usa o Claude Code para executar uma tarefa de programação num diretório."""
        result = subprocess.run(
            ["claude", "-p", prompt, "--dangerously-skip-permissions"],
            cwd=directory, capture_output=True, text=True, timeout=300
        )
        return (result.stdout or result.stderr or "Sem saída.")[:4000]
