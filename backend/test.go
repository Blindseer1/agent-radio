package main

import (
	"database/sql"
	"testing"

	_ "github.com/mattn/go-sqlite3"
)

// TestSetState verifies that the application state transitions correctly.
func TestSetState(t *testing.T) {
	// Reset to a known state
	currentState = Idle

	// Change state to Generating
	setState(Generating)

	if currentState != Generating {
		t.Errorf("Expected currentState to be Generating (2), got %v", currentState)
	}

	// Change state to Playing
	setState(Playing)

	if currentState != Playing {
		t.Errorf("Expected currentState to be Playing (4), got %v", currentState)
	}
}

// TestSaveToDB uses an isolated in-memory SQLite database to test database insertions
// without touching your actual production/development radio_library.db file.
func TestSaveToDB(t *testing.T) {
	// Open an isolated, in-memory SQLite database
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatalf("Failed to open in-memory database: %v", err)
	}
	defer db.Close()

	// Recreate the minimal schema required by saveToDB
	_, err = db.Exec(`
		CREATE TABLE songs (
			filepath TEXT PRIMARY KEY,
			title TEXT,
			artist TEXT,
			duration REAL,
			bpm REAL,
			energy REAL,
			brightness REAL,
			danceability REAL,
			mood_label TEXT
		);
	`)
	if err != nil {
		t.Fatalf("Failed to create mock table: %v", err)
	}

	// Construct a mock metadata payload structured exactly like the JSON
	// returned by your python analyzer script.
	mockMetadata := map[string]interface{}{
		"file_info": map[string]interface{}{
			"title":        "Banter & Beats",
			"artist":       "AI DJ Agent",
			"duration_sec": 184.5,
		},
		"audio_features": map[string]interface{}{
			"bpm":          122.0,
			"energy":       0.75,
			"brightness":   0.6,
			"danceability": 0.8,
			"mood_label":   "Upbeat",
		},
	}

	testPath := "/music/test_track.mp3"

	// Execute the function under test
	err = saveToDB(db, testPath, mockMetadata)
	if err != nil {
		t.Fatalf("saveToDB returned an unexpected error: %v", err)
	}

	// Query the in-memory database to verify the data was correctly written
	var title, artist, moodLabel string
	var bpm float64
	err = db.QueryRow(`
		SELECT title, artist, bpm, mood_label 
		FROM songs 
		WHERE filepath = ?`, testPath).Scan(&title, &artist, &bpm, &moodLabel)

	if err != nil {
		t.Fatalf("Failed to query inserted data: %v", err)
	}

	// Assertions
	if title != "Banter & Beats" {
		t.Errorf("Expected title 'Banter & Beats', got '%s'", title)
	}
	if artist != "AI DJ Agent" {
		t.Errorf("Expected artist 'AI DJ Agent', got '%s'", artist)
	}
	if bpm != 122.0 {
		t.Errorf("Expected BPM 122.0, got %f", bpm)
	}
	if moodLabel != "Upbeat" {
		t.Errorf("Expected mood_label 'Upbeat', got '%s'", moodLabel)
	}
}
