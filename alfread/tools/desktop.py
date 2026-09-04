"""
Desktop control tools — permite à Alfread interagir com a interface gráfica do computador.
Usa pyautogui para mouse, teclado e scroll. Usa subprocess para abrir aplicativos.
"""

import io
import subprocess
import time

from mcp.server.fastmcp import Image


def _pag():
    """Import lazy do pyautogui — só conecta ao display quando uma tool é chamada."""
    import pyautogui
    pyautogui.PAUSE = 0.3
    pyautogui.FAILSAFE = True
    return pyautogui


def _capture_screen() -> Image:
    """Captura a tela atual e retorna como Image do FastMCP (visível para o LLM)."""
    img = _pag().screenshot()
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return Image(data=buffer.getvalue(), format="png")


def register(mcp):

    @mcp.tool()
    def desktop_screenshot() -> Image:
        """
        Captura uma screenshot da tela atual do computador e retorna como imagem.
        Use isto SEMPRE antes de clicar em algo, para ver o estado atual da tela
        e identificar as coordenadas corretas dos elementos.
        """
        return _capture_screen()

    @mcp.tool()
    def desktop_click(x: int, y: int, button: str = "left", clicks: int = 1) -> dict:
        """
        Clica em uma posição específica na tela.

        Args:
            x: Coordenada horizontal em pixels.
            y: Coordenada vertical em pixels.
            button: Botão do mouse — "left", "right" ou "middle". Padrão: "left".
            clicks: Número de cliques (1 = simples, 2 = duplo). Padrão: 1.
        """
        _pag().click(x=x, y=y, button=button, clicks=clicks, interval=0.1)
        return {"action": "click", "x": x, "y": y, "button": button, "clicks": clicks, "status": "ok"}

    @mcp.tool()
    def desktop_move_mouse(x: int, y: int, duration: float = 0.3) -> dict:
        """
        Move o mouse para uma posição na tela sem clicar.

        Args:
            x: Coordenada horizontal em pixels.
            y: Coordenada vertical em pixels.
            duration: Tempo em segundos para mover (0 = instantâneo). Padrão: 0.3.
        """
        _pag().moveTo(x, y, duration=duration)
        return {"action": "move_mouse", "x": x, "y": y, "status": "ok"}

    @mcp.tool()
    def desktop_type(text: str) -> dict:
        """
        Digita um texto como se fosse no teclado. Funciona em Wayland e X11.
        Suporta acentos, unicode e caracteres especiais.
        O foco deve estar no campo correto antes de chamar.

        Args:
            text: O texto a ser digitado.
        """
        result = subprocess.run(
            ["ydotool", "type", "--", text],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"action": "type", "status": "error", "error": result.stderr.strip()}
        return {"action": "type", "text": text, "status": "ok"}

    @mcp.tool()
    def desktop_type_unicode(text: str) -> dict:
        """
        Alias para desktop_type. Digita texto com suporte completo a unicode.

        Args:
            text: O texto a ser digitado (suporta acentos, emojis, etc).
        """
        return desktop_type(text)

    @mcp.tool()
    def desktop_press_key(key: str) -> dict:
        """
        Pressiona uma tecla especial do teclado. Funciona em Wayland e X11.
        Exemplos de teclas válidas: enter, backspace, delete, tab, escape, space,
        up, down, left, right, home, end, pageup, pagedown, f1..f12,
        ctrl, alt, shift, super, insert.

        Args:
            key: Nome da tecla a pressionar.
        """
        # ydotool usa nomes de tecla do kernel Linux
        KEY_MAP = {
            "enter": "28", "return": "28", "backspace": "14", "delete": "111",
            "tab": "15", "escape": "1", "space": "57",
            "up": "103", "down": "108", "left": "105", "right": "106",
            "home": "102", "end": "107", "pageup": "104", "pagedown": "109",
            "insert": "110", "super": "125", "win": "125",
            "ctrl": "29", "alt": "56", "shift": "42",
            "f1": "59", "f2": "60", "f3": "61", "f4": "62", "f5": "63",
            "f6": "64", "f7": "65", "f8": "66", "f9": "67", "f10": "68",
            "f11": "87", "f12": "88",
        }
        keycode = KEY_MAP.get(key.lower())
        if not keycode:
            # Fallback para pyautogui se a tecla não estiver mapeada
            _pag().press(key)
            return {"action": "press_key", "key": key, "method": "pyautogui", "status": "ok"}

        result = subprocess.run(
            ["ydotool", "key", f"{keycode}:1", f"{keycode}:0"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"action": "press_key", "status": "error", "error": result.stderr.strip()}
        return {"action": "press_key", "key": key, "status": "ok"}

    @mcp.tool()
    def desktop_hotkey(keys: list[str]) -> dict:
        """
        Pressiona uma combinação de teclas ao mesmo tempo (atalho de teclado).
        Funciona em Wayland e X11.
        Exemplos:
          ["ctrl", "c"] — copiar
          ["ctrl", "v"] — colar
          ["alt", "f4"] — fechar janela
          ["ctrl", "alt", "t"] — abrir terminal (GNOME)
          ["super"] — abrir o launcher de apps

        Args:
            keys: Lista de teclas a pressionar simultaneamente.
        """
        KEY_MAP = {
            "enter": "28", "return": "28", "backspace": "14", "delete": "111",
            "tab": "15", "escape": "1", "space": "57",
            "up": "103", "down": "108", "left": "105", "right": "106",
            "home": "102", "end": "107", "pageup": "104", "pagedown": "109",
            "super": "125", "win": "125",
            "ctrl": "29", "alt": "56", "shift": "42",
            "a": "30", "b": "48", "c": "46", "d": "32", "e": "18", "f": "33",
            "g": "34", "h": "35", "i": "23", "j": "36", "k": "37", "l": "38",
            "n": "49", "o": "24", "p": "25", "r": "19", "s": "31", "t": "20",
            "v": "47", "w": "17", "x": "45", "z": "44",
            "f1": "59", "f2": "60", "f3": "61", "f4": "62", "f5": "63",
            "f6": "64", "f7": "65", "f8": "66", "f9": "67", "f10": "68",
            "f11": "87", "f12": "88",
        }
        # Press all keys down, then release all
        args = []
        for k in keys:
            code = KEY_MAP.get(k.lower())
            if not code:
                # Fallback para pyautogui
                _pag().hotkey(*keys)
                return {"action": "hotkey", "keys": keys, "method": "pyautogui", "status": "ok"}
            args.append(f"{code}:1")
        for k in reversed(keys):
            code = KEY_MAP.get(k.lower())
            args.append(f"{code}:0")

        result = subprocess.run(
            ["ydotool", "key"] + args,
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"action": "hotkey", "status": "error", "error": result.stderr.strip()}
        return {"action": "hotkey", "keys": keys, "status": "ok"}

    @mcp.tool()
    def desktop_scroll(x: int, y: int, direction: str = "down", amount: int = 3) -> dict:
        """
        Rola a tela (scroll) em uma posição específica.

        Args:
            x: Coordenada horizontal onde o scroll acontece.
            y: Coordenada vertical onde o scroll acontece.
            direction: "down" para rolar para baixo, "up" para rolar para cima. Padrão: "down".
            amount: Quantidade de "cliques" de scroll. Padrão: 3.
        """
        clicks = -amount if direction == "down" else amount
        _pag().scroll(clicks, x=x, y=y)
        return {"action": "scroll", "x": x, "y": y, "direction": direction, "amount": amount, "status": "ok"}

    @mcp.tool()
    def desktop_drag(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> dict:
        """
        Arrasta o mouse de um ponto até outro (clica, segura e solta).

        Args:
            x1: Coordenada X de origem.
            y1: Coordenada Y de origem.
            x2: Coordenada X de destino.
            y2: Coordenada Y de destino.
            duration: Tempo em segundos para completar o arraste. Padrão: 0.5.
        """
        pag = _pag()
        pag.moveTo(x1, y1, duration=0.2)
        pag.dragTo(x2, y2, duration=duration, button="left")
        return {"action": "drag", "from": [x1, y1], "to": [x2, y2], "status": "ok"}

    @mcp.tool()
    def desktop_open_app(app: str) -> dict:
        """
        Abre um aplicativo pelo nome ou comando no sistema Linux.
        Exemplos: "firefox", "nautilus", "code", "spotify", "gnome-terminal",
        "gedit", "vlc", "discord", "telegram-desktop", "google-chrome".

        Args:
            app: Nome ou comando do aplicativo a abrir.
        """
        try:
            subprocess.Popen(
                app.split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            time.sleep(1.5)
            return {"action": "open_app", "app": app, "status": "launched"}
        except FileNotFoundError:
            return {"action": "open_app", "app": app, "status": "error", "error": f"Aplicativo '{app}' não encontrado no PATH."}

    @mcp.tool()
    def desktop_write_and_submit(text: str) -> dict:
        """
        Digita um texto e pressiona Enter logo em seguida. Funciona em Wayland e X11.
        Útil para enviar mensagens, confirmar campos de busca, executar comandos no terminal.

        Args:
            text: O texto a digitar antes de pressionar Enter.
        """
        result = subprocess.run(
            ["ydotool", "type", "--", text],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"action": "write_and_submit", "status": "error", "error": result.stderr.strip()}
        time.sleep(0.1)
        # Enter key: keycode 28, press (1) then release (0)
        subprocess.run(["ydotool", "key", "28:1", "28:0"], capture_output=True, text=True)
        return {"action": "write_and_submit", "text": text, "status": "ok"}

    @mcp.tool()
    def desktop_get_mouse_position() -> dict:
        """
        Retorna a posição atual do cursor do mouse na tela.
        Útil para saber onde o cursor está antes de agir.
        """
        x, y = _pag().position()
        return {"x": x, "y": y}
