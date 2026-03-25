import speech_recognition as sr
import pyautogui
import unicodedata
import threading
import json
import time
import sys
import os

try:
    from core.recognizer import reconhecer as _reconhecer
except ImportError:
    _reconhecer = None  # fallback desabilitado se core não disponível

# ─── Carregar configurações ──────────────────────────────────────────────────
def carregar_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    defaults = {
        "wake_word": "mari",
        "language": "pt-BR",
        "listen_timeout": 5,
        "phrase_time_limit": 6,
        "log_unrecognized": False
    }
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            defaults.update(loaded)
    return defaults

CONFIG     = carregar_config()
WAKE_WORD  = CONFIG["wake_word"]
LANGUAGE   = CONFIG["language"]
TIMEOUT    = CONFIG["listen_timeout"]
PHRASE_LIM = CONFIG["phrase_time_limit"]
LOG_UNREC  = CONFIG["log_unrecognized"]

# ─── Normalização ─────────────────────────────────────────────────────────────
def normalizar(texto: str) -> str:
    """Remove acentos e converte para minúsculas para comparação robusta."""
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower()

# ─── Mapa de números por extenso (1–100) ─────────────────────────────────────
_UNIDADES = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3,
    "quatro": 4, "cinco": 5, "seis": 6, "sete": 7,
    "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12,
    "treze": 13, "catorze": 14, "quatorze": 14, "quinze": 15,
    "dezesseis": 16, "dezessete": 17, "dezoito": 18, "dezenove": 19,
    "vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50,
    "sessenta": 60, "setenta": 70, "oitenta": 80, "noventa": 90,
    "cem": 100,
}

MAPA_NUMEROS: dict = dict(_UNIDADES)
for _dezena_nome, _dezena_val in list(_UNIDADES.items()):
    if _dezena_val >= 20:
        for _unidade_nome, _unidade_val in list(_UNIDADES.items()):
            if 1 <= _unidade_val <= 9:
                MAPA_NUMEROS[f"{_dezena_nome} e {_unidade_nome}"] = _dezena_val + _unidade_val

def extrair_numero(texto: str):
    """Encontra o primeiro número (dígito ou extenso) no texto normalizado."""
    texto_norm = normalizar(texto)
    for parte in texto_norm.split():
        if parte.isdigit():
            return int(parte)
    for chave in sorted(MAPA_NUMEROS, key=len, reverse=True):
        if chave in texto_norm:
            return MAPA_NUMEROS[chave]
    return None

# ─── Mapeamento de comandos ───────────────────────────────────────────────────
def _press(key):
    return lambda: pyautogui.press(key)

def _hotkey(*keys):
    return lambda: pyautogui.hotkey(*keys)

COMANDOS = [
    (["proximo", "avanca", "avance", "seguinte", "frente"],
        "Avançar Slide", _press("right")),
    (["retorne", "volta", "volte", "anterior", "retorna"],
        "Voltar Slide", _press("left")),
    (["primeiro slide", "inicio", "comeco"],
        "Primeiro Slide", _hotkey("ctrl", "home")),
    (["ultimo slide", "final", "fim"],
        "Último Slide", _hotkey("ctrl", "end")),
    (["tela cheia", "iniciar apresentacao", "comecar apresentacao", "apresentar"],
        "Iniciar Apresentação (F5)", _press("f5")),
    (["encerrar apresentacao", "sair da apresentacao", "fechar apresentacao"],
        "Encerrar Apresentação (Esc)", _press("escape")),
    (["pausar", "tela preta", "pausa", "escurecer"],
        "Tela Preta (B)", _press("b")),
    (["ampliar", "zoom mais", "aumentar zoom"],
        "Zoom +", _hotkey("ctrl", "=")),
    (["reduzir", "zoom menos", "diminuir zoom"],
        "Zoom -", _hotkey("ctrl", "-")),
    (["laser", "ponteiro"],
        "Ponteiro Laser (L)", _press("l")),
]

# ─── Execução de comando ──────────────────────────────────────────────────────
def executar_comando(comando: str, motor: str = "") -> bool:
    raw  = comando.strip()
    norm = normalizar(raw)
    prefixo = f"[{motor}]" if motor else "↳"
    print(f"  {prefixo} Comando: '{raw}'")

    if any(p in norm for p in ["encerrar", "sair", "fechar"]):
        if not any(p in norm for p in ["apresentacao", "apresentação"]):
            print("  ↳ Ação: Encerrando Mari…")
            return False

    if "slide" in norm:
        slide_num = extrair_numero(norm)
        if slide_num is not None:
            print(f"  ↳ Ação: Ir para Slide {slide_num}")
            time.sleep(0.4)  # deixa o foco voltar ao PowerPoint
            for digito in str(slide_num):
                pyautogui.press(digito)
                time.sleep(0.05)
            time.sleep(0.1)
            pyautogui.press("enter")
            return True
        else:
            print("  ↳ Não entendi o número do slide.")
            return True

    for palavras_chave, descricao, acao in COMANDOS:
        if any(p in norm for p in palavras_chave):
            print(f"  ↳ Ação: {descricao}")
            acao()
            return True

    print("  ↳ Comando não reconhecido.")
    return True

# ─── Loop de escuta ───────────────────────────────────────────────────────────
def ouvir_microfone(
    pause_event: threading.Event | None = None,
    stop_event:  threading.Event | None = None,
    tray_app=None,
):
    recognizer = sr.Recognizer()

    if not sr.Microphone.list_microphone_names():
        print("Erro: Nenhum microfone encontrado.")
        return

    try:
        with sr.Microphone() as source:
            print("Ajustando ruído ambiente… aguarde.")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            if tray_app:
                tray_app.set_listening()

            print(f"\n✅ Mari está ouvindo!")
            print(f"   Palavra de ativação : '{WAKE_WORD}'")
            print(f"   Idioma              : {LANGUAGE}")
            print(f"   Comandos            : próximo, retorne, slide [N],")
            print(f"     tela cheia, pausar, primeiro slide, último slide,")
            print(f"     ampliar, reduzir, laser, encerrar\n")

            while True:
                # Verifica stop global (do tray ou externo)
                if stop_event and stop_event.is_set():
                    print("Mari: Encerrado pelo tray.")
                    break

                # Verifica pausa (do tray)
                if pause_event and pause_event.is_set():
                    time.sleep(0.3)
                    continue

                try:
                    audio = recognizer.listen(
                        source,
                        timeout=TIMEOUT,
                        phrase_time_limit=PHRASE_LIM,
                    )

                    motor = ""
                    if _reconhecer:
                        texto, motor = _reconhecer(
                            audio, recognizer, language=LANGUAGE,
                            modelo_vosk=CONFIG.get("vosk_model_path")
                        )
                    else:
                        try:
                            texto = recognizer.recognize_google(
                                audio, language=LANGUAGE
                            ).lower()
                            motor = "Online (Google)"
                        except (sr.RequestError, sr.UnknownValueError):
                            texto = None
                    if texto is None:
                        continue

                    wake_norm  = normalizar(WAKE_WORD)
                    texto_norm = normalizar(texto)

                    if wake_norm in texto_norm:
                        partes = texto_norm.split(wake_norm, 1)
                        if len(partes) > 1:
                            comando_limpo = partes[1].strip()
                            if comando_limpo:
                                if not executar_comando(comando_limpo, motor):
                                    if stop_event:
                                        stop_event.set()
                                    break
                            else:
                                print("Mari: Estou ouvindo. Diga um comando.")
                    elif LOG_UNREC:
                        print(f"Ouvi: '{texto}' (sem palavra de ativação)")

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except KeyboardInterrupt:
                    print("\nEncerrando via teclado…")
                    if stop_event:
                        stop_event.set()
                    break
                except Exception as e:
                    print(f"Erro inesperado: {e}")

    except OSError as e:
        print(f"Erro ao acessar o microfone: {e}")
        print("Verifique se o microfone está conectado e configurado corretamente.")


# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pause_event = threading.Event()
    stop_event  = threading.Event()

    # Tenta inicializar o tray (opcional — funciona sem)
    tray_app = None
    try:
        from ui.tray import start_tray
        tray_app = start_tray(pause_event, stop_event)
        print("🖥️  Ícone de bandeja iniciado. Clique com botão direito para opções.")
    except ImportError:
        print("ℹ️  pystray/Pillow não instalados — rodando sem ícone de bandeja.")
    except Exception as e:
        print(f"ℹ️  Tray não disponível: {e}")

    ouvir_microfone(pause_event, stop_event, tray_app)
