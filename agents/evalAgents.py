import json
import os

Director agent

# Did it pick from the 5 candidates? (hard fail if not)
# Does the picked file actually exist in melodii/?
# Is the BPM delta ≤ 40 between current and next song?
# Are the genres compatible? (grouped by family e.g. electronic/house/techno)
# Does the reason mention the correct title or artist?
# 
# DJ agent
# 
# Does the banter mention the correct title and artist?
# Is it the right length for TTS? (10–80 words, tweak as needed)
# Is it talking about the same song the Director picked?


# --- Configurare ---
FOLDER_MELODII = "melodii"
MAX_BPM_DELTA = 40          # diferenta maxima acceptata de BPM intre doua piese
MAX_BANTER_WORDS = 80       # limita de cuvinte pentru banter TTS
MIN_BANTER_WORDS = 10       # minim de cuvinte pentru banter TTS

GENRE_COMPATIBIL = {
    "pop": ["pop", "dance", "electropop", "indie pop"],
    "rock": ["rock", "indie rock", "alternative", "grunge"],
    "electronic": ["electronic", "techno", "house", "trance", "dance"],
    "hip-hop": ["hip-hop", "rap", "trap", "r&b"],
    "jazz": ["jazz", "blues", "soul", "funk"],
    "classical": ["classical", "orchestral", "ambient"],
}

def incarca_json(cale):
    with open(cale, 'r', encoding='utf-8') as f:
        return json.load(f)

def gaseste_melodie(nume_fisier):
    """Cauta o melodie in folderul de melodii dupa numele fisierului."""
    cale = os.path.join(FOLDER_MELODII, nume_fisier)
    if not os.path.exists(cale):
        return None
    return incarca_json(cale)

def genuri_compatibile(gen1, gen2):
    """Verifica daca doua genuri sunt compatibile pentru tranzitie."""
    gen1 = gen1.lower()
    gen2 = gen2.lower()
    if gen1 == gen2:
        return True
    for grup in GENRE_COMPATIBIL.values():
        if gen1 in grup and gen2 in grup:
            return True
    return False

# ==============================================================================
# EVALUARE DIRECTOR
# ==============================================================================
def evalueaza_director(output_director: dict) -> dict:
    """
    Evalueaza outputul agentului Director.

    Structura asteptata a output_director:
    {
        "melodie_curenta": "nume_fisier.json",
        "candidati": ["a.json", "b.json", "c.json", "d.json", "e.json"],
        "alegere": "b.json",
        "motiv": "BPM similar si acelasi gen..."
    }
    """
    scoruri = {}
    probleme = []
    ok = True

    melodie_curenta_date = gaseste_melodie(output_director.get("melodie_curenta", ""))
    alegere = output_director.get("alegere", "")
    candidati = output_director.get("candidati", [])
    motiv = output_director.get("motiv", "")

    # --- Criteriu 1: Alegerea e din lista candidatilor? ---
    alegere_valida = alegere in candidati
    scoruri["alegere_din_candidati"] = alegere_valida
    if not alegere_valida:
        probleme.append(f"❌ Alegerea '{alegere}' NU e in lista candidatilor: {candidati}")
        ok = False
    else:
        print(f"✅ Alegerea '{alegere}' e valida din lista candidatilor.")

    # --- Criteriu 2: Fisierul ales exista? ---
    melodie_aleasa_date = gaseste_melodie(alegere)
    scoruri["fisier_exista"] = melodie_aleasa_date is not None
    if melodie_aleasa_date is None:
        probleme.append(f"❌ Fisierul ales '{alegere}' nu exista in '{FOLDER_MELODII}'.")
        ok = False
    else:
        print(f"✅ Fisierul '{alegere}' exista.")

    # --- Criteriu 3: Delta BPM acceptabil? ---
    if melodie_curenta_date and melodie_aleasa_date:
        bpm_curent = melodie_curenta_date.get("bpm", 0)
        bpm_ales = melodie_aleasa_date.get("bpm", 0)
        delta_bpm = abs(bpm_curent - bpm_ales)
        scoruri["delta_bpm"] = delta_bpm
        scoruri["bpm_ok"] = delta_bpm <= MAX_BPM_DELTA
        if delta_bpm > MAX_BPM_DELTA:
            probleme.append(
                f"⚠️  Salt BPM prea mare: {bpm_curent} → {bpm_ales} (delta={delta_bpm}, max={MAX_BPM_DELTA})"
            )
        else:
            print(f"✅ Delta BPM ok: {bpm_curent} → {bpm_ales} (delta={delta_bpm})")

    # --- Criteriu 4: Gen compatibil? ---
    if melodie_curenta_date and melodie_aleasa_date:
        gen_curent = melodie_curenta_date.get("gen", "")
        gen_ales = melodie_aleasa_date.get("gen", "")
        compatibil = genuri_compatibile(gen_curent, gen_ales)
        scoruri["gen_compatibil"] = compatibil
        if not compatibil:
            probleme.append(
                f"⚠️  Gen incompatibil: '{gen_curent}' → '{gen_ales}'"
            )
        else:
            print(f"✅ Gen compatibil: '{gen_curent}' → '{gen_ales}'")

    # --- Criteriu 5: Motivul mentioneaza titlul sau artistul ales? ---
    if melodie_aleasa_date and motiv:
        titlu = melodie_aleasa_date.get("titlu", "").lower()
        artist = melodie_aleasa_date.get("artist", "").lower()
        motiv_lower = motiv.lower()
        mentioneza = titlu in motiv_lower or artist in motiv_lower
        scoruri["motiv_relevant"] = mentioneza
        if not mentioneza:
            probleme.append(
                f"⚠️  Motivul nu mentioneaza titlul ('{titlu}') sau artistul ('{artist}')."
            )
        else:
            print(f"✅ Motivul mentioneaza corect titlul/artistul.")

    return {
        "agent": "Director",
        "ok": ok and len(probleme) == 0,
        "scoruri": scoruri,
        "probleme": probleme,
    }

# ==============================================================================
# EVALUARE DJ
# ==============================================================================
def evalueaza_dj(output_dj: dict, output_director: dict) -> dict:
    """
    Evalueaza outputul agentului DJ.

    Structura asteptata a output_dj:
    {
        "banter": "Urmatoarea piesa e... de la...",
        "melodie_urmatoare": "b.json"
    }
    """
    scoruri = {}
    probleme = []

    banter = output_dj.get("banter", "")
    melodie_urmatoare = output_dj.get("melodie_urmatoare", "")
    alegere_director = output_director.get("alegere", "")

    melodie_date = gaseste_melodie(alegere_director)

    # --- Criteriu 1: Banter mentioneaza titlul corect? ---
    if melodie_date:
        titlu = melodie_date.get("titlu", "").lower()
        artist = melodie_date.get("artist", "").lower()
        banter_lower = banter.lower()

        mentioneaza_titlu = titlu in banter_lower
        mentioneaza_artist = artist in banter_lower
        scoruri["mentioneaza_titlu"] = mentioneaza_titlu
        scoruri["mentioneaza_artist"] = mentioneaza_artist

        if not mentioneaza_titlu:
            probleme.append(f"⚠️  Banterul nu mentioneaza titlul '{titlu}'.")
        else:
            print(f"✅ Banterul mentioneaza titlul corect.")

        if not mentioneaza_artist:
            probleme.append(f"⚠️  Banterul nu mentioneaza artistul '{artist}'.")
        else:
            print(f"✅ Banterul mentioneaza artistul corect.")

    # --- Criteriu 2: Lungime banter potrivita pentru TTS? ---
    nr_cuvinte = len(banter.split())
    scoruri["nr_cuvinte"] = nr_cuvinte
    scoruri["lungime_ok"] = MIN_BANTER_WORDS <= nr_cuvinte <= MAX_BANTER_WORDS
    if nr_cuvinte > MAX_BANTER_WORDS:
        probleme.append(
            f"⚠️  Banter prea lung pentru TTS: {nr_cuvinte} cuvinte (max {MAX_BANTER_WORDS})."
        )
    elif nr_cuvinte < MIN_BANTER_WORDS:
        probleme.append(
            f"⚠️  Banter prea scurt: {nr_cuvinte} cuvinte (min {MIN_BANTER_WORDS})."
        )
    else:
        print(f"✅ Lungime banter ok: {nr_cuvinte} cuvinte.")

    # --- Criteriu 3: DJ-ul vorbeste despre melodia aleasa de Director? ---
    scoruri["melodie_consistenta"] = melodie_urmatoare == alegere_director
    if melodie_urmatoare != alegere_director:
        probleme.append(
            f"❌ DJ vorbeste despre '{melodie_urmatoare}' dar Directorul a ales '{alegere_director}'."
        )
    else:
        print(f"✅ DJ si Director sunt in sync pe melodia '{alegere_director}'.")

    return {
        "agent": "DJ",
        "ok": len(probleme) == 0,
        "scoruri": scoruri,
        "probleme": probleme,
    }

# ==============================================================================
# RAPORT FINAL
# ==============================================================================
def printeaza_raport(rezultate: list):
    print("\n" + "="*55)
    print("📊 RAPORT EVALUARE AGENTI")
    print("="*55)
    for r in rezultate:
        status = "✅ PASS" if r["ok"] else "❌ FAIL"
        print(f"\n🤖 Agent: {r['agent']}  →  {status}")
        print(f"   Scoruri: {r['scoruri']}")
        if r["probleme"]:
            print("   Probleme detectate:")
            for p in r["probleme"]:
                print(f"     {p}")
    print("\n" + "="*55)

# ==============================================================================
# EXEMPLU DE RULARE
# ==============================================================================
if __name__ == "__main__":
    # Inlocuieste cu outputul real al agentilor tai
    output_director_exemplu = {
        "melodie_curenta": "song1.json",
        "candidati": ["song2.json", "song3.json", "song4.json", "song5.json", "song6.json"],
        "alegere": "song2.json",
        "motiv": "Am ales song2 de la Artist2 deoarece BPM-ul e similar si genul se potriveste."
    }

    output_dj_exemplu = {
        "banter": "Si acum, pregatiti-va pentru o tranzitie minunata! Urmatoarea piesa este Song Title 2 de la Artist2, o alegere perfecta pentru energia acestui moment!",
        "melodie_urmatoare": "song2.json"
    }

    print("🔎 Evaluare Director...\n" + "-"*40)
    rezultat_director = evalueaza_director(output_director_exemplu)

    print("\n🔎 Evaluare DJ...\n" + "-"*40)
    rezultat_dj = evalueaza_dj(output_dj_exemplu, output_director_exemplu)

    printeaza_raport([rezultat_director, rezultat_dj])
