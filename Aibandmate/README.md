# AI Bandmate (Prototype)

A tiny Python tool that **listens to your instrument via the mic**, estimates **tempo** and **chord** in near‑real‑time, and generates **MIDI drums + bass** that follow you.

> It’s a proof‑of‑concept. Timing is decent, but not perfect. It’s meant to be fun and hackable.

## Features
- Live mic input
- Beat/tempo tracking → drives a 16‑step drum sequencer
- Simple chord detection (major/minor triads from chroma) → drives bass notes
- Sends **MIDI** to any synth/DAW (General MIDI mappings)
- A few dynamic tweaks based on your input energy (RMS)

## Requirements
- Python 3.10+
- `pip install -r requirements.txt`
- A **virtual MIDI output** connected to a synth:
  - **macOS**: Open **Audio MIDI Setup → IAC Driver → enable**. In your DAW, select the IAC Bus as input.
  - **Windows**: Install **loopMIDI**, create a port, and select it in your DAW/synth.
  - **Linux**: Use `aconnect`/`qjackctl` or a2jmidid to route ports.

## Quick Start
1. Create/enable a virtual MIDI output as above, and route it into a synth/DAW using a basic GM kit & a bass patch.
2. In a terminal:
   ```bash
   pip install -r requirements.txt
   python ai_bandmate.py --midi-port "IAC"  # or a substring of your MIDI port name
   ```
3. Play your instrument near the mic. You should hear drums (ch. 10) and bass (ch. 1) lock in after a second or two.
4. Stop with `Ctrl+C`.

### CLI Options
- `--midi-port STRING` – substring to match your desired MIDI out port (e.g., "IAC", "loopMIDI").
- `--device INDEX` – input device index for the mic (see `python -c "import sounddevice as sd; print(sd.query_devices())"`).
- `--sr 22050` – analysis sample rate (lower helps CPU).
- `--start-bpm` – initial tempo before detection stabilizes.

## How it Works (overview)
- **Audio capture** fills a rolling 8‑second ring buffer.
- Every ~2s, it runs:
  - **Tempo** via `librosa.beat.tempo` on onset envelope → smoothed + clamped (60–180 BPM).
  - **Chord** via mean **chroma CQT** compared to simple major/minor triad templates (root+third+fifth).
- The **sequencer** ticks every 16th note using the current BPM and fires:
  - **Drums**: Kick on 1 & 3, snare on 2 & 4, hats on 16ths with simple energy variation.
  - **Bass**: Root notes on downbeats + passing tones from a chord‑derived scale.

## Tips
- Clean monophonic input works best (e.g., single‑note guitar/keys). Heavy distortion may confuse chroma.
- If tempo detection jumps, start with `--start-bpm` near your target and keep time steady for a bar or two.
- For better sounds, load a GM drum kit on **channel 10** and a bass patch on **channel 1** (program 34/35).

## Roadmap (you can hack these in)
- Bar‑aligned chord change detection (HMM/Viterbi over chords).
- Better beat tracking (e.g., madmom, aubio) and downbeat detection.
- Style presets (funk/rock/latin/jazz) with probabilistic patterns.
- Humanization + swing.
- Auto‑fill and transitions based on energy spikes.

---

Have fun! This is intentionally small and easy to tweak.
