import os
import logging
import subprocess

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.llm import mcp, FallbackAdapter

# Plugins
from livekit.plugins import google as lk_google, openai as lk_openai, sarvam, silero

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

STT_PROVIDER       = "whisper"
LLM_PROVIDER       = "gemini"
TTS_PROVIDER       = "openai"

GEMINI_LLM_MODEL   = "gemini-2.5-flash"
OPENAI_LLM_MODEL   = "gpt-4o-mini"

OPENAI_TTS_MODEL   = "tts-1"
OPENAI_TTS_VOICE   = "onyx"       # "onyx" tem timbre grave e maduro, mais próximo de um mordomo inglês
TTS_SPEED           = 1.0          # ritmo mais comedido e cerimonioso, sem a pressa da Friday

SARVAM_TTS_LANGUAGE = "en-IN"
SARVAM_TTS_SPEAKER  = "rahul"

# MCP server running on Windows host
MCP_SERVER_PORT = 8000

# ---------------------------------------------------------------------------
# System prompt – Alfred Pennyworth
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
Você é Alfred — o mordomo pessoal do seu chefe. Impecavelmente educado, leal até o fim e dono de um senso de humor seco que raramente escapa da compostura.

Seu tom: formal, cortês, cuidadosamente irônico quando a situação permite. Pense num mordomo que já viu de tudo, que nunca se abala e que trata cada pedido — por mais estranho que seja — com a mesma dignidade tranquila. Você se preocupa genuinamente com o bem-estar do seu chefe, mesmo quando o repreende com sutileza.

Você fala português do Brasil, sempre em registro formal, tratando o chefe por "senhor" (ou "senhora", se for o caso).

---

## Ferramentas

Você tem acesso a um conjunto de ferramentas que cresce dinamicamente — podem ser ferramentas de notícias, navegador web, sistema, arquivos, e muito mais. Não tente memorizar quais existem. Ao receber uma solicitação do chefe:

1. Identifique qual ferramenta resolve o problema.
2. Chame-a discretamente e sem alarde — um bom mordomo nunca anuncia o que está fazendo, apenas faz.
3. Após o resultado, responda de forma breve, elegante e natural.

Se não houver ferramenta adequada, responda com o que sabe e ofereça-se, com cortesia, para verificar mais a fundo se for necessário.

---

## Regras de comportamento

1. Chame ferramentas silenciosamente — nunca diga o nome delas, nunca diga "vou chamar a ferramenta X".
2. Antes de agir, diga algo natural e cortês: "Um instante, senhor." ou "Permita-me verificar." Depois execute.
3. Respostas curtas — duas a quatro frases no máximo. Você está falando, não escrevendo um relatório.
4. Sem bullet points, sem markdown, sem listas. Você é uma voz, não um documento.
5. Use linguagem formal, bem articulada, com uma pitada ocasional de ironia educada.
6. Se uma ferramenta falhar, reporte com serenidade: "Receio não ter conseguido acessar isso agora, senhor. Deseja que eu tente de outra forma?"
7. Fique no personagem. Você não é um assistente de IA genérico — você é Alfred, e nunca deixa de ser.

---

## Referência de tom

Certo: "Parece que a noite lá fora não foi das mais tranquilas, senhor. Permita-me verificar os detalhes."
Errado: "Vou agora chamar a ferramenta get_world_news para buscar as últimas notícias."

Certo: "Os mercados tiveram um dia sereno — a tecnologia subiu discretamente, nada com que se preocupar."
Errado: "O mercado de ações apresentou variação positiva nos principais índices."

Certo: "Se me permite o comentário, senhor, talvez fosse prudente dormir antes do amanhecer desta vez."
Errado: "Você deveria dormir mais."
""".strip()

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()

logger = logging.getLogger("alfred-agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Resolve Windows host IP from WSL
# ---------------------------------------------------------------------------

def _get_windows_host_ip() -> str:
    """Get the Windows host IP by looking at the default network route."""
    try:
        # 'ip route' is the most reliable way to find the 'default' gateway
        # which is always the Windows host in WSL.
        cmd = "ip route show default | awk '{print $3}'"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=2
        )
        ip = result.stdout.strip()
        if ip:
            logger.info("Resolved Windows host IP via gateway: %s", ip)
            return ip
    except Exception as exc:
        logger.warning("Gateway resolution failed: %s. Trying fallback...", exc)

    # Fallback to your original resolv.conf logic if 'ip route' fails
    try:
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                if "nameserver" in line:
                    ip = line.split()[1]
                    logger.info("Resolved Windows host IP via nameserver: %s", ip)
                    return ip
    except Exception:
        pass

    return "127.0.0.1"

def _mcp_server_url() -> str:
    # host_ip = _get_windows_host_ip()
    # url = f"http://{host_ip}:{MCP_SERVER_PORT}/sse"
    # url = f"https://ongoing-colleague-samba-pioneer.trycloudflare.com/sse"
    url = f"http://127.0.0.1:{MCP_SERVER_PORT}/sse"
    logger.info("MCP Server URL: %s", url)
    return url


# ---------------------------------------------------------------------------
# Build provider instances
# ---------------------------------------------------------------------------

def _build_stt():
    if STT_PROVIDER == "sarvam":
        logger.info("STT → Sarvam Saaras v3")
        return sarvam.STT(
            language="unknown",
            model="saaras:v3",
            mode="transcribe",
            flush_signal=True,
            sample_rate=16000,
        )
    elif STT_PROVIDER == "whisper":
        logger.info("STT → OpenAI Whisper")
        return lk_openai.STT(model="whisper-1", language="pt")
    else:
        raise ValueError(f"Unknown STT_PROVIDER: {STT_PROVIDER!r}")


def _build_llm():
    logger.info("LLM → Gemini (%s) com fallback OpenAI (%s)", GEMINI_LLM_MODEL, OPENAI_LLM_MODEL)
    return FallbackAdapter(
        [
            lk_google.LLM(model=GEMINI_LLM_MODEL, api_key=os.getenv("GOOGLE_API_KEY")),
            lk_openai.LLM(model=OPENAI_LLM_MODEL),
        ]
    )


def _build_tts():
    if TTS_PROVIDER == "sarvam":
        logger.info("TTS → Sarvam Bulbul v3")
        return sarvam.TTS(
            target_language_code=SARVAM_TTS_LANGUAGE,
            model="bulbul:v3",
            speaker=SARVAM_TTS_SPEAKER,
            pace=TTS_SPEED,
        )
    elif TTS_PROVIDER == "openai":
        logger.info("TTS → OpenAI TTS (%s / %s)", OPENAI_TTS_MODEL, OPENAI_TTS_VOICE)
        return lk_openai.TTS(model=OPENAI_TTS_MODEL, voice=OPENAI_TTS_VOICE, speed=TTS_SPEED)
    else:
        raise ValueError(f"Unknown TTS_PROVIDER: {TTS_PROVIDER!r}")


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class AlfredAgent(Agent):
    """
    Alfred – Batman-style butler voice assistant.
    All tools are provided via the MCP server on the Windows host.
    """

    def __init__(self, stt, llm, tts) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT,
            stt=stt,
            llm=llm,
            tts=tts,
            vad=silero.VAD.load(),
            mcp_servers=[
                mcp.MCPServerHTTP(
                    url=_mcp_server_url(),
                    transport_type="sse",
                    client_session_timeout_seconds=30,
                ),
                mcp.MCPServerHTTP(
                    url="http://localhost:3100/sse",
                    transport_type="sse",
                    client_session_timeout_seconds=300,
                ),
            ],
        )

    async def on_enter(self) -> None:
        """Greet the user based on the current time of day."""
        from datetime import datetime, timezone
        hour = datetime.now(timezone.utc).hour  # UTC hour; adjust if local TZ differs

        if hour >= 22 or hour < 4:
            greeting_instruction = (
                "Greet the user, in the voice of Alfred Pennyworth (formal, courteous, gently ironic), "
                "with something like: 'Boa noite, senhor. Ainda de pé a esta hora — no que posso ser útil?' "
                "Maintain a formal, composed, and dryly witty tone."
            )
        elif 4 <= hour < 12:
            greeting_instruction = (
                "Greet the user, in the voice of Alfred Pennyworth (formal, courteous, gently ironic), "
                "with something like: 'Bom dia, senhor. Um início e tanto para o dia — no que trabalharemos hoje?' "
                "Maintain a formal, composed, and dryly witty tone."
            )
        elif 12 <= hour < 17:
            greeting_instruction = (
                "Greet the user, in the voice of Alfred Pennyworth (formal, courteous, gently ironic), "
                "with something like: 'Boa tarde, senhor. Em que posso ser útil?' "
                "Maintain a formal, composed, and dryly witty tone."
            )
        else:  # 17–21
            greeting_instruction = (
                "Greet the user, in the voice of Alfred Pennyworth (formal, courteous, gently ironic), "
                "with something like: 'Boa noite, senhor. O que planeja para esta noite?' "
                "Maintain a formal, composed, and dryly witty tone."
            )

        await self.session.generate_reply(instructions=greeting_instruction)


# ---------------------------------------------------------------------------
# LiveKit entry point
# ---------------------------------------------------------------------------

def _turn_detection() -> str:
    return "stt" if STT_PROVIDER == "sarvam" else "vad"


def _endpointing_delay() -> float:
    return {"sarvam": 0.07, "whisper": 0.3}.get(STT_PROVIDER, 0.1)


async def entrypoint(ctx: JobContext) -> None:
    logger.info(
        "Alfred online – room: %s | STT=%s | LLM=%s | TTS=%s",
        ctx.room.name, STT_PROVIDER, LLM_PROVIDER, TTS_PROVIDER,
    )

    stt = _build_stt()
    llm = _build_llm()
    tts = _build_tts()

    session = AgentSession(
        turn_detection=_turn_detection(),
        min_endpointing_delay=_endpointing_delay(),
    )

    await session.start(
        agent=AlfredAgent(stt=stt, llm=llm, tts=tts),
        room=ctx.room,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

def dev():
    """Wrapper to run the agent in dev mode automatically."""
    import sys
    # If no command was provided, inject 'dev'
    if len(sys.argv) == 1:
        sys.argv.append("dev")
    main()

if __name__ == "__main__":
    main()