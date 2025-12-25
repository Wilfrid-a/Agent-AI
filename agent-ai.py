import speech_recognition as sr
import sounddevice as sd
import soundfile as sf
import pyttsx3
from openai import OpenAI
import os
from datetime import datetime
import webbrowser
from googlesearch import search

# Configuração da API OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuração da voz
voz = pyttsx3.init()
voz.setProperty("rate", 170)
voz.setProperty("volume", 1.0)

# Memória curta
memoria = [{"role": "system", "content": "Você é um assistente de voz educado, claro e objetivo. Responda sempre em português do Brasil."}]

def falar(texto):
    print("🤖 Assistente:", texto)
    voz.say(texto)
    voz.runAndWait()

def ouvir():
    r = sr.Recognizer()
    try:
        # Gravação usando sounddevice
        filename = "temp_audio.wav"
        fs = 44100  # taxa de amostragem
        falar("Pode falar sua pergunta após o sinal. Gravando 7 segundos...")
        duration = 7  # tempo de gravação em segundos
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        sf.write(filename, audio_data, fs)
        with sr.AudioFile(filename) as source:
            audio = r.record(source)
        texto = r.recognize_google(audio, language="pt-BR")
        print("🧑 Você:", texto)
        return texto
    except sr.UnknownValueError:
        falar("Não consegui entender o que você falou.")
        return ""
    except Exception as e:
        falar("Erro ao tentar capturar áudio.")
        print(e)
        return ""

def pesquisar_na_web(pergunta, num_resultados=1):
    resultados = list(search(pergunta, num_results=num_resultados, lang="pt"))
    if resultados:
        return resultados[0]
    return None

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

def responder(texto):
    if texto == "":
        return True
    t = texto.lower()
    if any(p in t for p in ["tchau", "encerrar", "sair", "até mais"]):
        falar("Até mais! Encerrando o assistente.")
        return False
    if "hora" in t:
        falar(f"Agora são {datetime.now().strftime('%H:%M')}.")
        return True
    if "abrir navegador" in t or "abrir google" in t:
        falar("Abrindo o navegador.")
        webbrowser.open("https://www.google.com")
        return True
    if "seu nome" in t:
        falar("Eu sou um assistente de voz com inteligência artificial.")
        return True
    # Pesquisa web
    falar("Pesquisando na internet...")
    link = pesquisar_na_web(texto)
    if link:
        falar(f"Encontrei este link: {link}. Vou resumir para você.")
        resposta = perguntar_chatgpt(f"Resuma o conteúdo desta página: {link}")
    else:
        resposta = "Desculpe, não encontrei resultados relevantes."
    falar(resposta)
    return True

def main():
    falar("Assistente iniciado. Pode falar comigo.")
    rodando = True
    while rodando:
        texto = ouvir()
        rodando = responder(texto)

if __name__ == "__main__":
    main()
