import os
import json
import time
import socket
import requests
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

# --- CONFIGURĂRI GENERALE ---
MODEL_AI = "qwen3:8b"
URL_OLLAMA = "http://localhost:11434/api/generate"
FOLDER_MELODII = "melodii" # Aici ții fișierele .json
FOLDER_AUDIO = "audio"     # Aici ții fișierele .mp3
FISIER_VOCE_DJ = os.path.abspath("duke_voice_temp.wav") # Calea absolută e necesară pentru Liquidsoap

# --- CONFIGURĂRI LIQUIDSOAP ---
# Asigură-te că în scriptul tău .liq ai setat telnet-ul (set("server.telnet", true))
# și ai o coadă de tipul: radio_q = request.queue(id="radio_q")
LIQUIDSOAP_HOST = "127.0.0.1"
LIQUIDSOAP_PORT = 1234
LIQUIDSOAP_QUEUE = "radio_q"

# --- 1. INIȚIALIZARE CHATTERBOX ---
print("⏳ Se încarcă motorul vocal Chatterbox pentru Duke Nukem...")
try:
    tts_model = ChatterboxTTS.from_pretrained(device="cuda")
except Exception:
    tts_model = ChatterboxTTS.from_pretrained(device="cpu")

# --- FUNCȚII AJUTĂTOARE ---
def incarca_baza_melodii(folder_path):
    lista_melodii = []
    if os.path.exists(folder_path):
        for fisier in os.listdir(folder_path):
            if fisier.endswith(".json"):
                try:
                    with open(os.path.join(folder_path, fisier), 'r', encoding='utf-8') as f:
                        lista_melodii.append(json.load(f))
                except Exception:
                    pass
    return lista_melodii

def trimite_la_liquidsoap(cale_fisier):
    """Trimite o comandă prin Telnet către coada Liquidsoap pentru a adăuga un fișier."""
    try:
        cale_absoluta = os.path.abspath(cale_fisier)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LIQUIDSOAP_HOST, LIQUIDSOAP_PORT))
            # Sintaxa standard Liquidsoap Telnet: <nume_coada>.push <cale_fisier>
            comanda = f"{LIQUIDSOAP_QUEUE}.push {cale_absoluta}\n"
            s.sendall(comanda.encode('utf-8'))
            
            # Citim confirmarea (opțional)
            raspuns = s.recv(1024).decode('utf-8')
            print(f"✅ Liquidsoap a preluat: {os.path.basename(cale_absoluta)}")
    except Exception as e:
        print(f"❌ Eroare la conectarea cu Liquidsoap: {e}")

# --- STAREA INIȚIALĂ ---
baza_melodii = incarca_baza_melodii(FOLDER_MELODII)
if not baza_melodii:
    print("Eroare: Adaugă cel puțin un JSON în folderul melodii!")
    exit()

# Piesă "dummy" de start
melodie_actuala = baza_melodii[0]

print("\n🚀 Sistemul AI 'Duke Nukem Radio' a fost inițializat!")
print("="*60)

# ==========================================
# CICLUL DE GENERAȚIE PENTRU URMĂTOAREA PIESĂ
# (Acest bloc poate fi pus într-un 'while True' sau apelat la cerere)
# ==========================================

# --- PASUL 1: DIRECTORUL ALEGE MELODIA ---
prompt_director = f"""
Tu o să iei rolul directorului unei stații radio numită "Agent radio", iar treaba ta este să analizezi melodia care cântă actual, să treci printr-o listă de fișiere JSON ce reprezintă tehnicalitățile melodiilor care îți va fi dată, să alegi o melodie asemănătoare cu cea actuală și să îi recomanzi DJ-ului care este alt agent AI ce va da play la melodia recomandată de tine. 

Te vei lua după bpm, gen și stil (ex: energetic, trist, ...). Tu vei pasa fișierul JSON al melodiei alese către agentul DJ.

Melodia actuală: {json.dumps(melodie_actuala)}
Opțiuni disponibile: {json.dumps(baza_melodii)}

REGULĂ: Răspunde EXCLUSIV cu un JSON valid de forma {{"choice": {{...}}}}
"""

print("🧠 Directorul analizează și alege piesa...")
resp_dir = requests.post(URL_OLLAMA, json={
    "model": MODEL_AI, "prompt": prompt_director, "stream": False, "format": "json"
})
melodie_aleasa = json.loads(resp_dir.json()["response"]).get("choice", baza_melodii[0])


# --- PASUL 2: DUKE NUKEM (DJ-UL) PREGĂTEȘTE TEXTUL ---
# Injectăm variabilele piesei în promptul lui Duke
prompt_dj = f"""
You are Duke Nukem, destroyer of aliens. You are a host at the Agent Station radio station where your job is to play songs handed to you by the director and you banter a little at the start and in-between songs. 

In the back there will be a director that will pick songs based on their technicallities so they are similar. You have to make little puns about the songs, the authors and the genre at your choice depending on the song you will play. Try to keep the commentary to only words, no interjections. Keep the introductions and talking short. Don't introduce yourself or mention who you are more than once or twice across the whole time.

The director just handed you this song to play next:
Title: {melodie_aleasa.get('titlu', 'Unknown')}
Artist: {melodie_aleasa.get('artist', 'Unknown')}
Genre: {melodie_aleasa.get('gen', 'Unknown')}

Now, write your short introduction for this track!
"""

print("🎙️ Duke Nukem își scrie replicile...")
resp_dj = requests.post(URL_OLLAMA, json={
    "model": MODEL_AI, "prompt": prompt_dj, "stream": False
})
text_duke = resp_dj.json()["response"].strip()

print(f"\n🎧 [DUKE NUKEM]: {text_duke}\n")


# --- PASUL 3: CHATTERBOX SINTETIZEAZĂ VOCEA ---
print("🔊 Se generează fișierul audio pentru voce...")
wav = tts_model.generate(text_duke)
ta.save(FISIER_VOCE_DJ, wav, tts_model.sr)


# --- PASUL 4: TRIMITEM TOTUL CĂTRE LIQUIDSOAP ---
# Numele fișierului mp3 trebuie să coincidă cu ID-ul sau titlul din JSON
fisier_melodie_mp3 = os.path.join(FOLDER_AUDIO, f"{melodie_aleasa.get('id', melodie_aleasa.get('titlu'))}.mp3")

print("📡 Se trimit fișierele în emisie (Liquidsoap)...")
# 1. Trimitem întâi vocea lui Duke Nukem
trimite_la_liquidsoap(FISIER_VOCE_DJ)

# 2. Trimitem apoi melodia
if os.path.exists(fisier_melodie_mp3):
    trimite_la_liquidsoap(fisier_melodie_mp3)
else:
    print(f"⚠️ ATENȚIE: Nu am găsit fișierul fizic {fisier_melodie_mp3} în folderul audio!")

# Actualizăm memoria pentru următoarea tură
melodie_actuala = melodie_aleasa
print("="*60)
print("✅ Proces finalizat. Coada Liquidsoap a fost actualizată.")
