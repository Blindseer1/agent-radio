#!/usr/bin/liquidsoap
settings.init.allow_root := true

# --- PROJ-79 (T5-04): Add Unix Domain Socket listener ---
# Enables communication from external apps (e.g., Go) at this socket path
settings.server.socket := true
settings.server.socket.path := "/tmp/liquidsoap.sock"
settings.server.socket.permissions := 0o777

# Kept from original script: Track start webhooks
def on_new_track(m) =
  ignore(http.post("http://167.172.171.185:8080/track-started",
    headers=[("Content-Type", "application/json")],
    data=json.stringify(m)))
end

# --- PROJ-78 (T5-03): Base playlist source ---
music_playlist = playlist(reload=5, reload_mode="watch", "/music/")

# --- PROJ-80 (T5-05): Implement queue.push handler ---
# Creates a distinct queue for high-priority DJ drops/voice tracks
dj_queue = request.queue(id="dj_drop_queue")

# --- PROJ-81, 82, 83 (T5-06, T5-07, T5-08): Ducking, Crossfade, and Restore Logic ---
# Custom transition function managing the cross-fading and automated volume adjustment
def dj_transition(music, dj) =
  # Sequence them: play DJ track first, then transition back to music
  sequence([
    # PROJ-81: Drop background music volume to 15% immediately when DJ starts
    amplify(0.15, music),
    
    # PROJ-82 & PROJ-83: 3-second crossfade from DJ track back into the music 
    # This also naturally restores music back to 100% volume after the fade finishes
    crossfade(duration=3.0, fade_in=3.0, fade_out=0.0, dj, music)
  ])
end

# Use a switch to interrupt normal music when a track is pushed into the DJ queue
# 'track_sensitive=false' ensures that the DJ track can cut in immediately
radio_stream = switch(track_sensitive=false, [
  ({!dj_queue}, dj_transition(music_playlist, dj_queue)),
  ({true}, music_playlist)
])

# --- PROJ-85 (T5-10): Handle empty queue gracefully fallback to silence ---
# Wrap the combined stream in mksafe to fallback to safe silence if both sources run empty
final_stream = mksafe(radio_stream)

# Attach track listener
final_stream.on_track(on_new_track)

# Output stream to Icecast mount
output.icecast(
  %mp3,
  host = "localhost",
  port = 8000,
  password = "mds",
  mount = "/radio",
  final_stream
)
