import speech_recognition as sr
import pyttsx3
from openai import OpenAI
import os
from datetime import datetime
import webbrowser
import logging
import sounddevice as sd
import numpy as np

# ===============================
# CONFIGURAÇÃO
# ===============================
logging.basicConfig(level=logging.INFO)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===============================
# CONFIGURAÇÃO DA VOZ
# ===============================
def configurar_voz():
    engine = pyttsx3.init()
    engine.setProperty("rate", 180)
    engine.setProperty("volume", 0.9)

    voices = engine.getProperty('voices')
    for voice in voices:
        if 'portugu' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break

    return engine

voz = configurar_voz()

# ===============================
# MEMÓRIA
# ===============================
memoria = [
    {
        "role": "system",
        "content": (
            "Você é um assistente de voz brasileiro chamado Klér. "
            "Seja educado, claro e objetivo. "
            "Responda sempre em português do Brasil de forma natural."
        )
    }
]

# ===============================
# FUNÇÕES PRINCIPAIS
# ===============================
def falar(texto):
    print(f"🤖 Klér: {texto}")
    voz.say(texto)
    voz.runAndWait()

def ouvir():
    r = sr.Recognizer()

    fs = 16000          # taxa de amostragem
    duracao = 5         # segundos
    canais = 1

    print("🎤 Ouvindo...")

    try:
        audio_np = sd.rec(
            int(duracao * fs),
            samplerate=fs,
            channels=canais,
            dtype='int16'
        )
        sd.wait()
    except Exception as e:
        logging.error(f"Erro ao acessar o microfone: {e}")
        return ""

    audio_bytes = audio_np.tobytes()
    audio = sr.AudioData(audio_bytes, fs, 2)

    try:
        texto = r.recognize_google(audio, language="pt-BR")
        print(f"🧑 Você: {texto}")
        return texto
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        logging.error(f"Erro no reconhecimento: {e}")
        return ""

def perguntar_chatgpt(pergunta):
    memoria.append({"role": "user", "content": pergunta})

    if len(memoria) > 20:
        memoria.pop(1)

    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=memoria,
            max_tokens=400,
            temperature=0.7
        )

        texto_resposta = resposta.choices[0].message.content
        memoria.append({"role": "assistant", "content": texto_resposta})
        return texto_resposta
    except Exception as e:
        logging.error(e)
        return "Desculpe, estou com problemas para me conectar no momento."

def mostrar_ajuda():
    falar(
        "Eu sou o Klér, seu assistente virtual. "
        "Posso informar hora e data, abrir sites como Google e YouTube "
        "e responder perguntas sobre diversos assuntos."
    )

def responder(texto):
    if not texto:
        return True

    t = texto.lower()

    comandos = {
        "tchau|encerrar|sair|até mais|adeus":
            lambda: (falar("Até mais! Foi um prazer ajudar."), False),

        "hora atual|que horas são":
            lambda: (falar(f"São {datetime.now().strftime('%H:%M')}."), True),

        "data de hoje|que dia é hoje":
            lambda: (falar(f"Hoje é {datetime.now().strftime('%d/%m/%Y')}."), True),

        "abrir navegador|abrir google":
            lambda: (falar("Abrindo navegador."),
                     webbrowser.open("https://google.com"),
                     True),

        "abrir youtube":
            lambda: (falar("Abrindo YouTube."),
                     webbrowser.open("https://youtube.com"),
                     True),

        "seu nome|quem é você":
            lambda: (falar("Meu nome é Klér, seu assistente virtual!"), True),

        "ajuda|comandos|o que você faz":
            lambda: (mostrar_ajuda(), True)
    }

    for padrao, acao in comandos.items():
        if any(p in t for p in padrao.split("|")):
            resultado = acao()
            return resultado[-1] if isinstance(resultado, tuple) else resultado

    falar("Deixa eu pensar...")
    resposta = perguntar_chatgpt(texto)
    falar(resposta)
    return True

def main():
    falar("Olá! Eu sou o Klér, seu assistente pessoal. Como posso te ajudar hoje?")

    while True:
        texto = ouvir()
        if not responder(texto):
            break

if __name__ == "__main__":
    main()
