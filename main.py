# Symbolic, Conditioned Generation
import pandas as pd

# Load dataset
df = pd.read_csv("Music Info.csv")

# Drop rows with missing values for key symbolic features
df = df.dropna(subset=['key', 'mode', 'tempo', 'time_signature', 'genre'])

# Bin tempo
def bin_tempo(tempo):
    if tempo < 80:
        return 'slow'
    elif tempo < 120:
        return 'medium'
    else:
        return 'fast'

df['tempo_bin'] = df['tempo'].apply(bin_tempo)

# Combine symbolic tokens
df['symbolic_sequence'] = df.apply(lambda row: f"key_{int(row.key)} mode_{'major' if row.mode == 1 else 'minor'} tempo_{row.tempo_bin} time_{int(row.time_signature)}", axis=1)

# Group sequences by genre
genre_groups = df.groupby('genre')['symbolic_sequence'].apply(list)

# Step 2: Tokenize + LSTM Training (per genre or genre-conditioned)
from keras.preprocessing.text import Tokenizer
from keras.utils import to_categorical
import numpy as np

# Flatten genre sequences
all_tokens = []
genre_token_map = {}

for genre, seqs in genre_groups.items():
    tokens = [s.split() for s in seqs]
    flat = [token for sublist in tokens for token in sublist]
    all_tokens.extend(flat)
    genre_token_map[genre] = flat

# Tokenize
tokenizer = Tokenizer()
tokenizer.fit_on_texts([all_tokens])
vocab_size = len(tokenizer.word_index) + 1

# Prepare sequences for a chosen genre
chosen_genre = 'rock'  # or any genre in dataset
tokens = genre_token_map[chosen_genre]
seq_length = 4
X, y = [], []

token_ids = tokenizer.texts_to_sequences([tokens])[0]

for i in range(seq_length, len(token_ids)):
    X.append(token_ids[i - seq_length:i])
    y.append(token_ids[i])

X = np.array(X)
y = to_categorical(y, num_classes=vocab_size)

# Step 3: Build and Train LSTM Model
from keras.models import Sequential
from keras.layers import Embedding, LSTM, Dense

model = Sequential()
model.add(Embedding(input_dim=vocab_size, output_dim=50, input_length=seq_length))
model.add(LSTM(128))
model.add(Dense(vocab_size, activation='softmax'))

model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X, y, batch_size=256, epochs=20)

# Step 4: Generate Music Sequences

def generate_tokens(seed, num_steps=32):
    result = seed[:]
    for _ in range(num_steps):
        encoded = tokenizer.texts_to_sequences([result[-seq_length:]])[0]
        encoded = np.reshape(encoded, (1, seq_length))
        pred = model.predict(encoded, verbose=0)
        next_index = np.argmax(pred)
        next_token = tokenizer.index_word[next_index]
        result.append(next_token)
    return result

# Step 5: Convert Symbolic Sequence to MIDI

from mido import Message, MidiFile, MidiTrack, bpm2tempo

def symbolic_to_midi(tokens, filename="conditioned_output.mid"):
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)
    
    key = 0
    tempo = 120
    time_sig = 4

    for token in tokens:
        if "key_" in token:
            key = int(token.split("_")[1])
        elif "tempo_" in token:
            tempo = {"slow": 60, "medium": 100, "fast": 140}[token.split("_")[1]]
        elif "time_" in token:
            time_sig = int(token.split("_")[1])
        elif "mode_" in token:
            continue  # Mode not used here directly

        # Insert note as placeholder (C + key)
        note = 60 + key
        track.append(Message('note_on', note=note, velocity=64, time=0))
        track.append(Message('note_off', note=note, velocity=64, time=480))

    midi.save(filename)

# Example usage
tokens = generate_tokens(seed=["key_0", "mode_major", "tempo_medium", "time_4"])
symbolic_to_midi(tokens)
