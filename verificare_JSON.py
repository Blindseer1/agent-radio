import json
import os

# --- Configurare ---
FOLDER_MELODII = "melodii"

# Acestea sunt cheile pe care se bazează Directorul și DJ-ul tău.
# Dacă un JSON e valid sintactic, dar nu are "gen", AI-ul poate avea probleme.
CHEI_OBLIGATORII = ["titlu", "artist", "bpm", "gen", "stil"]

def valideaza_fisiere_json(folder_path):
    if not os.path.exists(folder_path):
        print(f"❌ Folderul '{folder_path}' nu a fost găsit.")
        return

    fisiere = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    
    if not fisiere:
        print(f"⚠️ Nu s-au găsit fișiere .json în '{folder_path}'.")
        return

    fisiere_perfecte = 0
    fisiere_cu_erori = 0

    print(f"🔎 Se scanează {len(fisiere)} fișiere în '{folder_path}'...\n" + "="*50)

    for fisier in fisiere:
        cale_completa = os.path.join(folder_path, fisier)
        
        try:
            with open(cale_completa, 'r', encoding='utf-8') as f:
                date = json.load(f)
                
                # Verificăm dacă lipsesc chei esențiale din structură
                chei_lipsa = [cheie for cheie in CHEI_OBLIGATORII if cheie not in date]
                
                if chei_lipsa:
                    print(f"⚠️ [STRUCTURĂ INCOMPLETĂ] {fisier}: JSON valid, dar lipsesc cheile -> {chei_lipsa}")
                    fisiere_cu_erori += 1
                else:
                    print(f"✅ [OK] {fisier}")
                    fisiere_perfecte += 1

        except json.JSONDecodeError as e:
            # Prinde erorile de sintaxă (ex: acoladă lipsă) și îți arată unde e greșeala
            print(f"❌ [EROARE SINTAXĂ] {fisier}: {e.msg} (Linia {e.lineno}, Coloana {e.colno})")
            fisiere_cu_erori += 1
            
        except Exception as e:
            # Prinde alte erori (ex: nu ai permisiuni să citești fișierul)
            print(f"❌ [EROARE CITIRE] {fisier}: {e}")
            fisiere_cu_erori += 1

    print("="*50)
    print(f"📊 REZULTAT FINAL:")
    print(f"   Fișiere valide și complete: {fisiere_perfecte}")
    print(f"   Fișiere cu probleme: {fisiere_cu_erori}")

if __name__ == "__main__":
    valideaza_fisiere_json(FOLDER_MELODII)
