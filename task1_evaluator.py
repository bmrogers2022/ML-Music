import sys
from collections import Counter
from music21 import converter, note, key
import matplotlib.pyplot as plt

def analyze_midi_key_compliance(file_path):
    # Parse the MIDI file
    try:
        midi_stream = converter.parse(file_path)
    except Exception as e:
        print(f"❌ Failed to parse MIDI: {e}")
        return

    # Detect key
    try:
        detected_key = midi_stream.analyze('key')
    except Exception as e:
        print(f"❌ Failed to detect key: {e}")
        return

    allowed_notes = set(p.name for p in detected_key.pitches)

    print(f"\n🎼 Detected Key: {detected_key}")
    print(f"🎵 Allowed Notes: {sorted(allowed_notes)}\n")

    note_names = []
    non_conforming = []

    # Collect note data
    for element in midi_stream.recurse():
        if isinstance(element, note.Note):
            name = element.pitch.name  # e.g. "C#", "A"
            note_names.append(name)
            if name not in allowed_notes:
                non_conforming.append((name, element.offset))

    total_notes = len(note_names)

    # Display compliance results
    if non_conforming:
        print(f"❌ Found {len(non_conforming)} non-conforming notes (out of {total_notes}):")
        for pitch, offset in non_conforming:
            print(f" - {pitch} at offset {offset}")
    else:
        print("✅ All notes conform to the detected key.")

    # Plot note frequency
    plot_note_frequencies(note_names, detected_key)

    note_names = []
    non_conforming = []
    beat_note_counts = defaultdict(Counter)
    time_signatures = []

    for element in midi_stream.recurse():
        if isinstance(element, meter.TimeSignature):
            time_signatures.append((element.ratioString, element.offset))

        if isinstance(element, note.Note):
            name = element.pitch.name
            beat = round(element.beat, 2)  # round for grouping
            note_names.append(name)

            if name not in allowed_notes:
                non_conforming.append((name, element.offset))

            beat_note_counts[beat][name] += 1

    # Print time signature info
    print("\n🕐 Time Signature(s) detected:")
    for ts, offset in time_signatures:
        print(f" - {ts} at offset {offset}")

    # ... [existing compliance and plotting code]

    print("\n📊 Note occurrences per beat position (aggregated):")
    for beat in sorted(beat_note_counts):
        print(f" Beat {beat}:")
        for pitch, count in beat_note_counts[beat].items():
            print(f"   - {pitch}: {count}")

    plot_notes_by_beat(beat_note_counts)

def plot_notes_by_beat(beat_note_counts):
    import matplotlib.pyplot as plt

    # Organize data
    beats = sorted(beat_note_counts.keys())
    all_pitches = sorted({p for counter in beat_note_counts.values() for p in counter})

    data = []
    for pitch in all_pitches:
        data.append([beat_note_counts[beat].get(pitch, 0) for beat in beats])

    # Stack plot
    plt.figure(figsize=(12, 6))
    for i, pitch_data in enumerate(data):
        plt.plot(beats, pitch_data, label=all_pitches[i])

    plt.title("Note Occurrences by Beat Position")
    plt.xlabel("Beat Number in Measure")
    plt.ylabel("Occurrences")
    plt.legend(loc="upper right", fontsize="small", ncol=2)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    


def plot_note_frequencies(note_list, detected_key):
    note_counts = Counter(note_list)
    labels, counts = zip(*sorted(note_counts.items(), key=lambda x: x[0]))

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, counts, color='skyblue', edgecolor='black')

    # Highlight notes in the key
    in_key = set(p.name for p in detected_key.pitches)
    for bar, label in zip(bars, labels):
        if label not in in_key:
            bar.set_color('salmon')

    plt.title(f"Note Occurrences in MIDI (Key: {detected_key})")
    plt.xlabel("Note Name (no octave)")
    plt.ylabel("Frequency")
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_key_plot.py <midi_file.mid>")
        sys.exit(1)

    midi_file_path = sys.argv[1]
    analyze_midi_key_compliance(midi_file_path)
