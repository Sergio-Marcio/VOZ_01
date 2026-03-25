"""
core/recognizer.py — Reconhecimento de voz com fallback offline via Vosk.

Fluxo:
    1. Tenta Google Speech API (online, alta precisão)
    2. Se sr.RequestError (sem internet), usa Vosk (offline, local)
    3. Se Vosk não estiver configurado, lança ImportError com instruções
"""

import json
import os
import speech_recognition as sr

# ─── Estado do Vosk (carrega modelo apenas uma vez) ──────────────────────────
_vosk_model = None
_vosk_rec   = None
_vosk_available = False


def _inicializar_vosk(modelo_path: str | None = None) -> bool:
    """
    Tenta carregar o modelo Vosk.
    Retorna True se carregamento bem-sucedido, False caso contrário.
    """
    global _vosk_model, _vosk_rec, _vosk_available

    try:
        from vosk import Model, KaldiRecognizer
    except ImportError:
        print("ℹ️  [Vosk] Pacote não instalado. Execute: pip install vosk")
        return False

    # Caminho padrão do modelo
    if modelo_path is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        modelo_path = os.path.join(base, "vosk-model-pt")

    if not os.path.isdir(modelo_path):
        print(f"ℹ️  [Vosk] Modelo não encontrado em: {modelo_path}")
        print("     Baixe em: https://alphacephei.com/vosk/models")
        print("     Descompacte como 'vosk-model-pt/' na raiz do projeto.")
        return False

    try:
        from vosk import Model, KaldiRecognizer
        _vosk_model    = Model(modelo_path)
        _vosk_rec      = KaldiRecognizer(_vosk_model, 16000)
        _vosk_available = True
        print(f"✅ [Vosk] Modelo offline carregado: {modelo_path}")
        return True
    except Exception as e:
        print(f"⚠️  [Vosk] Falha ao carregar modelo: {e}")
        return False


def _reconhecer_vosk(audio: sr.AudioData) -> str | None:
    """Converte AudioData → texto usando Vosk offline."""
    global _vosk_rec

    if not _vosk_available or _vosk_rec is None:
        return None

    try:
        # Vosk trabalha com raw PCM 16-bit mono 16kHz
        raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
        _vosk_rec.AcceptWaveform(raw)
        resultado = json.loads(_vosk_rec.Result())
        texto = resultado.get("text", "").strip()
        return texto if texto else None
    except Exception as e:
        print(f"⚠️  [Vosk] Erro no reconhecimento: {e}")
        return None


# ─── Função pública ───────────────────────────────────────────────────────────
def reconhecer(
    audio: sr.AudioData,
    recognizer: sr.Recognizer,
    language: str = "pt-BR",
    modelo_vosk: str | None = None,
) -> tuple[str | None, str]:
    """
    Tenta reconhecer áudio usando Google (online) e,
    em caso de falha de conexão, usa Vosk (offline).

    Retorna uma tupla (texto, motor_usado).
    motor_usado será "Online (Google)" ou "Offline (Vosk)".
    """
    global _vosk_available

    # ── Tentativa online: Google ──────────────────────────────────────────
    try:
        texto = recognizer.recognize_google(audio, language=language)
        return texto.lower(), "Online (Google)"
    except sr.RequestError:
        print("⚠️  [Google] Sem internet — ativando fallback Vosk…")
    except sr.UnknownValueError:
        return None, "Google"  # Áudio ininteligível — não tenta Vosk

    # ── Tentativa offline: Vosk ───────────────────────────────────────────
    if not _vosk_available:
        _inicializar_vosk(modelo_vosk)

    if _vosk_available:
        texto = _reconhecer_vosk(audio)
        if texto:
            return texto.lower(), "Offline (Vosk)"

    return None, "Nenhum"
