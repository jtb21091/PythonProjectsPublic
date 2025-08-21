#!/usr/bin/env python3
"""
AI Bandmate (v1.2)
------------------
Reactive "AI bandmate" prototype that listens to your mic, estimates tempo & chord
in near‑real‑time, and drives MIDI drums + bass that follow your playing.

What’s new in v1.2
- Creates a **virtual MIDI output** automatically if none are present
- Prints the **exact MIDI port** name opened
- Adds `--list-midi` and `--list-devices` helpers
- Uses librosa's modern API: `librosa.feature.rhythm.tempo`
- Adds a `--metronome` option (16th‑note tick) so you can confirm MIDI is reaching your DAW

Tip: In GarageBand, use a single Software Instrument track (record‑armed) to sanity‑check that MIDI
is arriving. In Logic/Ableton, you can route by channel (drums=ch10, bass=ch1).
"""

from __future__ import annotations

import argparse
import threading
import time
from typing import Tuple

import numpy as np
import sounddevice as sd
import mido

import librosa
from librosa.feature.rhythm import tempo as lr_tempo

# ---------------------- Configuration ----------------------

DEFAULT_SR = 22050            # sample rate for analysis (lower SR reduces CPU)
FRAME_SIZE = 2048             # audio callback blocksize
RING_SECONDS = 8.0            # rolling window seconds for analysis
ANALYZE_EVERY = 2.0           # seconds between analysis runs
MIN_BPM, MAX_BPM = 60, 180    # tempo clamp
BPM_SMOOTH = 0.7              # smoothing factor for BPM updates (0..1), higher = stickier
LOUD_THRESH = 0.03            # rough RMS threshold for "energy" adjustments

# Drum pattern (16‑step)
KICK_STEPS  = {0, 8}
SNARE_STEPS = {4, 12}
HAT_STEPS   = set(range(16))  # closed hat every 16th by default

# GM drum note numbers
MIDI_KICK   = 36
MIDI_SNARE  = 38
MIDI_HAT_C  = 42  # closed hat
MIDI_HAT_O  = 46  # open hat
MIDI_TICK   = 76  # high woodblock for metronome

# GM Instrument Programs (0‑based): 33 = Fingered Bass
BASS_PROGRAM = 33

# Default chord if detection fails
DEFAULT_CHORD = ("C", "maj")  # (root_name, quality)

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
NAME_TO_PC = {n:i for i,n in enumerate(NOTE_NAMES)}

def pc_to_name(pc:int)->str:
    return NOTE_NAMES[pc % 12]

# --------------- Simple chord detection (triad templates) ---------------

MAJOR_TEMPLATE = np.array([1,0,0,0,1,0,0,1,0,0,0,0], dtype=float)  # root, +4, +7
MINOR_TEMPLATE = np.array([1,0,0,1,0,0,0,1,0,0,0,0], dtype=float)  # root, +3, +7

def best_chord_from_chroma(chroma_mean: np.ndarray) -> Tuple[str, str, float]:
    """Return (root_name, 'maj'|'min', score)."""
    v = np.maximum(chroma_mean, 0)
    if v.sum() > 0:
        v = v / (v.sum() + 1e-9)
    best = (DEFAULT_CHORD[0], DEFAULT_CHORD[1], -1.0)
    for root in range(12):
        maj = np.roll(MAJOR_TEMPLATE, root)
        minu = np.roll(MINOR_TEMPLATE, root)
        score_maj = float((v * maj).sum())
        score_min = float((v * minu).sum())
        if score_maj > best[2]:
            best = (pc_to_name(root), "maj", score_maj)
        if score_min > best[2]:
            best = (pc_to_name(root), "min", score_min)
    return best

# --------------- Audio Input / Analysis Threads ---------------

class AudioAnalyzer:
    def __init__(self, sr:int=DEFAULT_SR):
        self.sr = sr
        self.blocksize = FRAME_SIZE
        self.ring_len = int(RING_SECONDS * sr)
        self.ring = np.zeros(self.ring_len, dtype=np.float32)
        self.rpos = 0

        self.buffer_lock = threading.Lock()
        self.last_analysis_time = 0.0

        self.current_bpm = 100.0
        self.current_chord = DEFAULT_CHORD
        self.energy = 0.0  # RMS

        self._stop = threading.Event()

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            # non-fatal statuses can occur; ignore for prototype
            pass
        # Audio arrives already at the stream's samplerate (we open with self.sr)
        audio = indata[:, 0] if indata.ndim > 1 else indata
        audio = audio.astype(np.float32)

        with self.buffer_lock:
            n = len(audio)
            end = self.rpos + n
            if end <= self.ring_len:
                self.ring[self.rpos:end] = audio
            else:
                first = self.ring_len - self.rpos
                self.ring[self.rpos:] = audio[:first]
                self.ring[:n-first] = audio[first:]
            self.rpos = (self.rpos + n) % self.ring_len

    def get_ring_copy(self) -> np.ndarray:
        with self.buffer_lock:
            idx = np.arange(self.rpos, self.rpos + self.ring_len) % self.ring_len
            return np.copy(self.ring[idx])

    def analyze_once(self):
        y = self.get_ring_copy().astype(np.float32)
        if np.allclose(y, 0):
            return

        # Energy (RMS) for simple dynamics
        rms = float(np.sqrt(np.mean(y**2) + 1e-9))
        self.energy = 0.9*self.energy + 0.1*rms

        # Tempo (BPM)
        try:
            onset_env = librosa.onset.onset_strength(y=y, sr=self.sr)
            tempos = lr_tempo(onset_envelope=onset_env, sr=self.sr, aggregate=None)
            if tempos is not None and len(tempos) > 0:
                bpm_raw = float(np.median(tempos))
                bpm_raw = max(MIN_BPM, min(MAX_BPM, bpm_raw))
                self.current_bpm = BPM_SMOOTH * self.current_bpm + (1.0 - BPM_SMOOTH) * bpm_raw
        except Exception:
            pass

        # Chord (from chroma)
        try:
            chroma = librosa.feature.chroma_cqt(y=y, sr=self.sr)
            chroma_mean = np.mean(chroma, axis=1)
            root, qual, _ = best_chord_from_chroma(chroma_mean)
            self.current_chord = (root, qual)
        except Exception:
            pass

    def analysis_loop(self):
        while not self._stop.is_set():
            now = time.time()
            if now - self.last_analysis_time >= ANALYZE_EVERY:
                self.analyze_once()
                self.last_analysis_time = now
            time.sleep(0.01)

    def stop(self):
        self._stop.set()


# --------------- MIDI Sequencer ---------------

def find_output_port(name_hint:str|None=None):
    """Open existing MIDI out if available; otherwise create a virtual port.
    Returns (port_object, opened_name)
    """
    ports = mido.get_output_names()
    if ports:
        if name_hint:
            for p in ports:
                if name_hint.lower() in p.lower():
                    return mido.open_output(p), p
        return mido.open_output(ports[0]), ports[0]
    # No ports found: create virtual
    try:
        po = mido.open_output("AI Bandmate (virtual)", virtual=True)
        return po, "AI Bandmate (virtual)"
    except Exception as e:
        raise RuntimeError(
            "No MIDI outputs were found and creating a virtual port failed.\n"
            f"Underlying error: {e}\n"
            "On macOS you can also enable the IAC Driver via Audio MIDI Setup."
        )


def chord_root_to_midi(root_name:str, base_octave:int=2) -> int:
    pc = NAME_TO_PC.get(root_name, 0)
    return 12*base_octave + pc  # e.g., C2..B2


def scale_for_chord(root_pc:int, quality:str):
    if quality == "min":
        intervals = [0, 3, 7, 10]  # triad + b7
    else:
        intervals = [0, 4, 7, 10]  # triad + b7 (mixolydian-ish)
    return [(root_pc + i) % 12 for i in intervals]


def midi_note_on(out, ch:int, note:int, vel:int=90):
    out.send(mido.Message('note_on', note=int(note), velocity=int(vel), channel=int(ch)))


def midi_note_off(out, ch:int, note:int):
    out.send(mido.Message('note_off', note=int(note), velocity=0, channel=int(ch)))


def midi_program_change(out, ch:int, program:int):
    out.send(mido.Message('program_change', channel=int(ch), program=int(program)))


class BandmateSequencer:
    def __init__(self, analyzer: AudioAnalyzer, outport, drum_channel:int=9, bass_channel:int=0,
                 metronome: bool=False, met_vel:int=90):
        self.analyzer = analyzer
        self.out = outport
        self.drum_ch = drum_channel
        self.bass_ch = bass_channel
        self._stop = threading.Event()

        self.metronome = metronome
        self.met_vel = int(np.clip(met_vel, 1, 127))

        # Set bass instrument
        midi_program_change(self.out, self.bass_ch, BASS_PROGRAM)

        self.step = 0
        self.cur_notes = []  # active bass notes to turn off

    def schedule_loop(self):
        # Main 16‑step pattern scheduler
        next_time = time.perf_counter()
        while not self._stop.is_set():
            bpm = max(MIN_BPM, min(MAX_BPM, self.analyzer.current_bpm))
            spb = 60.0 / bpm
            sixteenth = spb / 4.0

            # read analysis state
            root_name, quality = self.analyzer.current_chord
            energy = self.analyzer.energy

            # optional metronome tick
            if self.metronome:
                self.out.send(mido.Message('note_on', note=MIDI_TICK, velocity=self.met_vel, channel=self.drum_ch))
                self.out.send(mido.Message('note_off', note=MIDI_TICK, velocity=0, channel=self.drum_ch))

            # drums
            self.play_drums(self.step, energy)

            # bass
            self.play_bass(self.step, root_name, quality, energy)

            # advance time
            next_time += sixteenth
            delay = next_time - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            else:
                next_time = time.perf_counter()
            self.step = (self.step + 1) % 16

        # cleanup
        for note in self.cur_notes:
            midi_note_off(self.out, self.bass_ch, note)
        self.cur_notes.clear()

    def play_drums(self, step:int, energy:float):
        # Basic rock beat with dynamic hats; more energy -> occasional open hats
        hat_note = MIDI_HAT_O if (energy > LOUD_THRESH and step in {2,6,10,14}) else MIDI_HAT_C

        if step in HAT_STEPS:
            self.out.send(mido.Message('note_on', note=hat_note, velocity=70, channel=self.drum_ch))
            self.out.send(mido.Message('note_off', note=hat_note, velocity=0, channel=self.drum_ch))

        if step in KICK_STEPS:
            self.out.send(mido.Message('note_on', note=MIDI_KICK, velocity=100, channel=self.drum_ch))
            self.out.send(mido.Message('note_off', note=MIDI_KICK, velocity=0, channel=self.drum_ch))

        if step in SNARE_STEPS:
            self.out.send(mido.Message('note_on', note=MIDI_SNARE, velocity=110, channel=self.drum_ch))
            self.out.send(mido.Message('note_off', note=MIDI_SNARE, velocity=0, channel=self.drum_ch))

    def play_bass(self, step:int, root_name:str, quality:str, energy:float):
        # Turn off previously playing notes (short bass notes)
        for note in self.cur_notes:
            midi_note_off(self.out, self.bass_ch, note)
        self.cur_notes.clear()

        root_midi = chord_root_to_midi(root_name, base_octave=2)  # C2≈36
        root_pc = NAME_TO_PC.get(root_name, 0)

        # Choose a scale set from chord quality
        pcs = scale_for_chord(root_pc, quality)

        # Pattern: roots on 0,4,8,12; passing tones on 3,7,11,15
        if step in {0, 4, 8, 12}:
            note = root_midi
        elif step in {3, 7, 11, 15}:
            interval_pc = pcs[1 + (step // 4) % (len(pcs)-1)]
            semis = (interval_pc - root_pc) % 12
            note = root_midi + semis
        else:
            # occasional ghost notes if energy is high
            if energy > LOUD_THRESH and step in {2,6,10,14}:
                note = root_midi + 12  # octave up ghost
            else:
                return

        vel = 75 if energy < LOUD_THRESH else 95
        midi_note_on(self.out, self.bass_ch, note, vel=vel)
        self.cur_notes.append(note)

    def stop(self):
        self._stop.set()


# ---------------------- Main ----------------------

def main():
    parser = argparse.ArgumentParser(description="AI Bandmate: reactive drums+bass from live audio")
    parser.add_argument("--device", type=int, default=None, help="Input device index for microphone (sounddevice).")
    parser.add_argument("--sr", type=int, default=DEFAULT_SR, help="Analysis sample rate.")
    parser.add_argument("--midi-port", type=str, default=None, help="Hint to match a MIDI output port by substring.")
    parser.add_argument("--start-bpm", type=float, default=100.0, help="Initial BPM before detection stabilizes.")
    parser.add_argument("--list-midi", action="store_true", help="List MIDI output names and exit.")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices and exit.")
    parser.add_argument("--metronome", action="store_true", help="Send a 16th‑note tick on the drum channel (ch10).")
    parser.add_argument("--met-vel", type=int, default=90, help="Metronome tick velocity (1–127).")
    args = parser.parse_args()

    if args.list_midi:
        print("Available MIDI outputs:", mido.get_output_names())
        return
    if args.list_devices:
        print(sd.query_devices())
        return

    analyzer = AudioAnalyzer(sr=args.sr)
    analyzer.current_bpm = float(args.start_bpm)

    # Open MIDI (creates a virtual port if none exist)
    out, opened_name = find_output_port(args.midi_port)
    print(f"[MIDI] Output opened: {opened_name}")

    sequencer = BandmateSequencer(
        analyzer, out,
        drum_channel=9, bass_channel=0,
        metronome=args.metronome, met_vel=args.met_vel,
    )

    # Start threads
    analysis_thread = threading.Thread(target=analyzer.analysis_loop, daemon=True)
    analysis_thread.start()

    seq_thread = threading.Thread(target=sequencer.schedule_loop, daemon=True)
    seq_thread.start()

    # Audio stream — we explicitly open with analyzer.sr so callback gets the same rate
    print("Opening audio input stream...")
    with sd.InputStream(callback=analyzer.audio_callback, channels=1, samplerate=analyzer.sr,
                        blocksize=FRAME_SIZE, device=args.device):
        print('Running! If you are not hearing anything, pick the MIDI input named "AI Bandmate (virtual)" (or your IAC bus) in your DAW.')
        print("Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(0.5)
                root, qual = analyzer.current_chord
                print(f"BPM ~ {analyzer.current_bpm:5.1f} | Chord: {root}{'' if qual=='maj' else 'm'} | Energy: {analyzer.energy:0.3f}", end="\r")
        except KeyboardInterrupt:
            print("\nStopping...")


if __name__ == "__main__":
    main()
