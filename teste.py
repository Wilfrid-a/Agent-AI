import json
import queue
import threading
import time
import math
import requests
import pyttsx3
import pyaudio
import tkinter as tk
from tkinter import ttk
from vosk import Model, KaldiRecognizer
from bs4 import BeautifulSoup

# ================= CONFIGURAÇÕES =================
VOSK_MODEL_PATH = "vosk-model-small-pt-0.3"  # <<< AJUSTE AQUI
SAMPLE_RATE = 16000
# ================================================

# ================== VOZ (TTS) ====================
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 170)
tts_engine.setProperty("volume", 1.0)

def falar(texto):
    tts_engine.say(texto)
    tts_engine.runAndWait()

# ================== BUSCA WEB ====================
def buscar_web(consulta):
    try:
        url = f"https://duckduckgo.com/html/?q={consulta}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resposta = requests.get(url, headers=headers, timeout=5)

        soup = BeautifulSoup(resposta.text, "html.parser")
        resultados = soup.find_all("a", class_="result__a", limit=3)

        textos = [r.get_text() for r in resultados]
        if textos:
            return " ".join(textos)
        else:
            return "Não encontrei informações relevantes."
    except Exception:
        return "Erro ao buscar na internet."

# ================== RECONHECIMENTO =================
class ReconhecedorVoz(threading.Thread):
    def __init__(self, callback_texto):
        super().__init__(daemon=True)
        self.callback_texto = callback_texto
        self.rodando = True

        self.modelo = Model(VOSK_MODEL_PATH)
        self.rec = KaldiRecognizer(self.modelo, SAMPLE_RATE)

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=8000
        )

    def run(self):
        while self.rodando:
            dados = self.stream.read(4000, exception_on_overflow=False)
            if self.rec.AcceptWaveform(dados):
                resultado = json.loads(self.rec.Result())
                texto = resultado.get("text", "")
                if texto:
                    self.callback_texto(texto)

    def parar(self):
        self.rodando = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

# ================== HOLOGRAMA =====================
class Holograma(tk.Canvas):
    def __init__(self, master):
        super().__init__(master, bg="black", highlightthickness=0)
        self.angle = 0
        self.after(50, self.animar)

    def animar(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        cx, cy = w // 2, h // 2

        for i in range(12):
            ang = self.angle + i * 30
            r = 80 + 10 * math.sin(time.time() * 2 + i)
            x = cx + r * math.cos(math.radians(ang))
            y = cy + r * math.sin(math.radians(ang))
            self.create_oval(x-8, y-8, x+8, y+8, fill="#00ffff", outline="")

        self.angle += 3
        self.after(50, self.animar)

# ================== APP PRINCIPAL =================
class AssistenteApp:
    def __init__(self, root):
        self.root = root
        root.title("Assistente Holográfico")
        root.geometry("800x600")

        abas = ttk.Notebook(root)
        abas.pack(fill="both", expand=True)

        # Aba Holograma
        frame_holo = ttk.Frame(abas)
        abas.add(frame_holo, text="Holograma")

        self.holograma = Holograma(frame_holo)
        self.holograma.pack(fill="both", expand=True)

        # Aba Texto
        frame_texto = ttk.Frame(abas)
        abas.add(frame_texto, text="Texto")

        self.texto = tk.Text(frame_texto, wrap="word", font=("Arial", 12))
        self.texto.pack(fill="both", expand=True)

        # Reconhecedor
        self.reconhecedor = ReconhecedorVoz(self.processar_texto)
        self.reconhecedor.start()

        falar("Assistente iniciado. Estou ouvindo.")

    def processar_texto(self, texto):
        self.texto.insert("end", f"\nVocê: {texto}\n")
        self.texto.see("end")

        resposta = self.gerar_resposta(texto)

        self.texto.insert("end", f"Assistente: {resposta}\n")
        self.texto.see("end")

        falar(resposta)

    def gerar_resposta(self, texto):
        if "pesquise" in texto or "buscar" in texto:
            consulta = texto.replace("pesquise", "").replace("buscar", "")
            return buscar_web(consulta)

        return f"Você disse: {texto}. Posso pesquisar algo se quiser."

    def fechar(self):
        self.reconhecedor.parar()
        self.root.destroy()

# ================== EXECUÇÃO ======================
if __name__ == "__main__":
    root = tk.Tk()
    app = AssistenteApp(root)
    root.protocol("WM_DELETE_WINDOW", app.fechar)
    root.mainloop()
