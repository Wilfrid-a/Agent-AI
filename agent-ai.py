import speech_recognition as sr
import pyttsx3
from openai import OpenAI
import os
from datetime import datetime
import webbrowser

# ===============================
# CONFIGURAÇÃO DA API OPENAI
# ===============================

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===============================
# CONFIGURAÇÃO DA VOZ
# ===============================

voz = pyttsx3.init()
voz.setProperty("rate", 170)
voz.setProperty("volume", 1.0)

# ===============================
# MEMÓRIA CURTA DA CONVERSA
# ===============================

memoria = [
    {
        "role": "system",
        "content": (
            "Você é um assistente de voz educado, claro e objetivo. "
            "Responda sempre em português do Brasil."
        )
    }
]

# ===============================
# FUNÇÃO FALAR
# ===============================

def falar(texto):
    print("🤖 Assistente:", texto)
    voz.say(texto)
    voz.runAndWait()

# ===============================
# FUNÇÃO OUVIR
# ===============================

def ouvir():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Ouvindo...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source)

    try:
        texto = r.recognize_google(audio, language="pt-BR")
        print("🧑 Você:", texto)
        return texto
    except sr.UnknownValueError:
        falar("Não entendi. Pode repetir?")
        return ""
    except sr.RequestError:
        falar("Erro no reconhecimento de voz.")
        return ""

# ===============================
# CHATGPT
# ===============================

def perguntar_chatgpt(pergunta):
    memoria.append({"role": "user", "content": pergunta})

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=memoria,
        max_tokens=300
    )

    texto_resposta = resposta.choices[0].message.content
    memoria.append({"role": "assistant", "content": texto_resposta})

    return texto_resposta

# ===============================
# INTELIGÊNCIA PRINCIPAL
# ===============================

def responder(texto):
    if texto == "":
        return True

    t = texto.lower()

    # ENCERRAR
    if any(p in t for p in ["tchau", "encerrar", "sair", "até mais"]):
        falar("Até mais! Encerrando o assistente.")
        return False

    # HORA
    if "hora" in t:
        falar(f"Agora são {datetime.now().strftime('%H:%M')}.")
        return True

    # ABRIR NAVEGADOR
    if "abrir navegador" in t or "abrir google" in t:
        falar("Abrindo o navegador.")
        webbrowser.open("https://www.google.com")
        return True

    # NOME
    if "seu nome" in t:
        falar("Eu sou um assistente de voz com inteligência artificial.")
        return True

    # CHATGPT
    falar("Pensando...")
    resposta = perguntar_chatgpt(texto)
    falar(resposta)

    return True

# ===============================
# PROGRAMA PRINCIPAL
# ===============================

def main():
    falar("Assistente iniciado. Pode falar comigo.")
    rodando = True
    while rodando:
        texto = ouvir()
        rodando = responder(texto)

# ===============================
# INICIAR
# ===============================

if __name__ == "__main__":
    main()
