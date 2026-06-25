#!/usr/bin/env python3
"""Read a text script and convert it to an audio file (text-to-speech).

By default the script reads ``script.txt`` from the current directory and
writes an audio file next to it. Two backends are supported:

* ``gtts``    - Google Text-to-Speech. Produces a natural-sounding MP3 but
                requires an internet connection. (pip install gTTS)
* ``pyttsx3`` - Fully offline TTS that uses the system speech engine
                (eSpeak/NSSpeechSynthesizer/SAPI5). Writes a WAV file.
                (pip install pyttsx3)

The default backend is ``auto``: it tries gTTS first and falls back to
pyttsx3 if gTTS is unavailable or fails (e.g. no network).

Examples
--------
    python text_to_audio.py
    python text_to_audio.py --input script.txt --output speech.mp3
    python text_to_audio.py --engine pyttsx3 --output speech.wav
"""

import argparse
import os
import sys


def read_script(path):
    """Return the trimmed contents of *path* or exit with a clear error."""
    if not os.path.isfile(path):
        sys.exit(f"Error: input file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read().strip()
    if not text:
        sys.exit(f"Error: input file is empty: {path}")
    return text


def synthesize_gtts(text, output, lang="en", slow=False):
    """Convert *text* to speech with gTTS (online). Returns True on success."""
    try:
        from gtts import gTTS
    except ImportError:
        print("gTTS is not installed (pip install gTTS).", file=sys.stderr)
        return False

    try:
        gTTS(text=text, lang=lang, slow=slow).save(output)
    except Exception as exc:  # network errors, bad language, etc.
        print(f"gTTS failed: {exc}", file=sys.stderr)
        return False
    return True


def synthesize_pyttsx3(text, output, rate=None, volume=None):
    """Convert *text* to speech with pyttsx3 (offline). Returns True on success."""
    try:
        import pyttsx3
    except ImportError:
        print("pyttsx3 is not installed (pip install pyttsx3).", file=sys.stderr)
        return False

    try:
        engine = pyttsx3.init()
        if rate is not None:
            engine.setProperty("rate", rate)
        if volume is not None:
            engine.setProperty("volume", volume)
        engine.save_to_file(text, output)
        engine.runAndWait()
    except Exception as exc:
        print(f"pyttsx3 failed: {exc}", file=sys.stderr)
        return False
    return True


def default_output(engine):
    """Pick a sensible output filename/extension for the chosen engine."""
    return "speech.wav" if engine == "pyttsx3" else "speech.mp3"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert a text script to an audio file.")
    parser.add_argument("-i", "--input", default="script.txt",
                        help="path to the input text file (default: script.txt)")
    parser.add_argument("-o", "--output", default=None,
                        help="path to the output audio file "
                             "(default: speech.mp3 for gtts, speech.wav for pyttsx3)")
    parser.add_argument("-e", "--engine", default="auto",
                        choices=["auto", "gtts", "pyttsx3"],
                        help="TTS backend to use (default: auto)")
    parser.add_argument("-l", "--lang", default="en",
                        help="language code for gTTS (default: en)")
    parser.add_argument("--slow", action="store_true",
                        help="speak slowly (gTTS only)")
    parser.add_argument("--rate", type=int, default=None,
                        help="speech rate in words/min (pyttsx3 only)")
    parser.add_argument("--volume", type=float, default=None,
                        help="volume from 0.0 to 1.0 (pyttsx3 only)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    text = read_script(args.input)
    output = args.output or default_output(args.engine)

    if args.engine == "gtts":
        ok = synthesize_gtts(text, output, lang=args.lang, slow=args.slow)
    elif args.engine == "pyttsx3":
        ok = synthesize_pyttsx3(text, output, rate=args.rate, volume=args.volume)
    else:  # auto: try online gTTS first, fall back to offline pyttsx3
        ok = synthesize_gtts(text, output, lang=args.lang, slow=args.slow)
        if not ok:
            output = args.output or default_output("pyttsx3")
            print("Falling back to offline pyttsx3 engine...", file=sys.stderr)
            ok = synthesize_pyttsx3(text, output, rate=args.rate, volume=args.volume)

    if not ok:
        sys.exit("Error: could not generate audio. Install gTTS or pyttsx3 "
                 "(pip install gTTS pyttsx3) and try again.")

    print(f"Audio written to {output}")


if __name__ == "__main__":
    main()
