#!/usr/bin/env python3
"""Read a text script and convert it to an audio file (text-to-speech).

By default the script reads ``script.txt`` from the current directory and
writes an audio file next to it. Three backends are supported:

* ``edge``    - Microsoft Edge neural voices. The best free quality (very
                natural, many voices) and needs only an internet connection,
                no API key. Writes an MP3. (pip install edge-tts)
* ``gtts``    - Google Text-to-Speech. Decent MP3, needs internet.
                (pip install gTTS)
* ``pyttsx3`` - Fully offline TTS that uses the system speech engine
                (eSpeak/NSSpeechSynthesizer/SAPI5). Writes a WAV file.
                (pip install pyttsx3)

The default backend is ``auto``: it tries edge-tts first (best quality),
then gTTS, then falls back to offline pyttsx3 if there's no network.

List available neural voices with::

    python text_to_audio.py --list-voices

Examples
--------
    python text_to_audio.py
    python text_to_audio.py --voice en-US-ChristopherNeural
    python text_to_audio.py --engine gtts --output speech.mp3
    python text_to_audio.py --engine pyttsx3 --output speech.wav
"""

import argparse
import os
import sys

# A deep, authoritative voice that suits an in-flight captain announcement.
DEFAULT_EDGE_VOICE = "en-US-ChristopherNeural"


def _https_proxy():
    """Return the configured HTTPS proxy (if any) for edge-tts to route through."""
    return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")


def find_ffmpeg():
    """Locate an ffmpeg executable (bundled imageio-ffmpeg or one on PATH)."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        import shutil
        return shutil.which("ffmpeg")


# ffmpeg filter that makes a clean voice track sound like a cabin PA / intercom.
# Kept deliberately gentle (wide band, light compression, no bit-crusher) so the
# voice still sounds human rather than robotic.
_INTERCOM_CHAIN = (
    "highpass=f=300,lowpass=f=3400,"
    "acompressor=threshold=-16dB:ratio=3:attack=10:release=80,"
    "volume=4dB,alimiter=limit=0.97"
)


def apply_intercom(src, dst, chime=True, crackle=False):
    """Post-process *src* into *dst* with an intercom effect.

    Optionally prepends a two-tone cabin *chime* and mixes in radio *crackle*
    (fluctuating band-limited static) under the voice.
    """
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("ffmpeg not found (pip install imageio-ffmpeg) - skipping intercom "
              "effect.", file=sys.stderr)
        return False

    import subprocess

    inputs = ["-i", src]
    parts = ["[0]" + _INTERCOM_CHAIN + "[vfilt]"]
    voice = "[vfilt]"
    idx = 1

    if crackle:
        # Band-limited, fluctuating static mixed under the voice for a radio feel.
        inputs += ["-f", "lavfi", "-i", "anoisesrc=color=pink:amplitude=0.5"]
        parts.append(f"[{idx}]highpass=f=600,lowpass=f=3200,volume=0.08,"
                     f"tremolo=f=6:d=0.6[noise]")
        parts.append(f"{voice}[noise]amix=inputs=2:duration=first:normalize=0[vmix]")
        voice = "[vmix]"
        idx += 1

    parts.append(f"{voice}aformat=channel_layouts=mono:sample_rates=24000[voice]")
    voice = "[voice]"

    if chime:
        # Two-tone "ding-dong" cabin chime ahead of the announcement.
        inputs += ["-f", "lavfi", "-i", "sine=frequency=698:duration=0.7"]
        inputs += ["-f", "lavfi", "-i", "sine=frequency=523:duration=0.9"]
        parts.append(f"[{idx}]afade=t=out:st=0.15:d=0.55,volume=0.5[t1]")
        parts.append(f"[{idx + 1}]adelay=600|600,afade=t=out:st=0.2:d=0.7,volume=0.5[t2]")
        parts.append("[t1][t2]amix=inputs=2:normalize=0,highpass=f=400,lowpass=f=3000,"
                     "aformat=channel_layouts=mono:sample_rates=24000[chime]")
        parts.append(f"[chime]{voice}concat=n=2:v=0:a=1[out]")
        out_label = "[out]"
    else:
        out_label = voice

    cmd = [ffmpeg, "-y", *inputs, "-filter_complex", ";".join(parts),
           "-map", out_label, dst]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except Exception as exc:
        print(f"Intercom processing failed: {exc}", file=sys.stderr)
        return False
    return True


def read_script(path):
    """Return the trimmed contents of *path* or exit with a clear error."""
    if not os.path.isfile(path):
        sys.exit(f"Error: input file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read().strip()
    if not text:
        sys.exit(f"Error: input file is empty: {path}")
    return text


def synthesize_edge(text, output, voice=DEFAULT_EDGE_VOICE, rate=None, pitch=None):
    """Convert *text* to speech with edge-tts (online, neural). Returns True on success."""
    try:
        import asyncio
        import edge_tts
    except ImportError:
        print("edge-tts is not installed (pip install edge-tts).", file=sys.stderr)
        return False

    kwargs = {"voice": voice, "proxy": _https_proxy()}
    if rate:
        kwargs["rate"] = rate    # e.g. "+10%" / "-15%"
    if pitch:
        kwargs["pitch"] = pitch  # e.g. "+5Hz" / "-10Hz"

    try:
        async def _run():
            await edge_tts.Communicate(text, **kwargs).save(output)
        asyncio.run(_run())
    except Exception as exc:
        print(f"edge-tts failed: {exc}", file=sys.stderr)
        return False
    return True


def list_edge_voices():
    """Print the available edge-tts neural voices, then return True/False on success."""
    try:
        import asyncio
        import edge_tts
    except ImportError:
        print("edge-tts is not installed (pip install edge-tts).", file=sys.stderr)
        return False
    try:
        async def _run():
            return await edge_tts.list_voices(proxy=_https_proxy())
        voices = asyncio.run(_run())
    except Exception as exc:
        print(f"Could not fetch voices: {exc}", file=sys.stderr)
        return False
    for v in sorted(voices, key=lambda x: x["ShortName"]):
        print(f"{v['ShortName']:<28} {v['Gender']:<8} {v['Locale']}")
    return True


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
                             "(default: speech.mp3, or speech.wav for pyttsx3)")
    parser.add_argument("-e", "--engine", default="auto",
                        choices=["auto", "edge", "gtts", "pyttsx3"],
                        help="TTS backend to use (default: auto -> edge, gtts, pyttsx3)")
    parser.add_argument("-v", "--voice", default=DEFAULT_EDGE_VOICE,
                        help=f"neural voice for edge-tts (default: {DEFAULT_EDGE_VOICE})")
    parser.add_argument("--list-voices", action="store_true",
                        help="list available edge-tts neural voices and exit")
    parser.add_argument("--edge-rate", default=None,
                        help="edge-tts speaking rate, e.g. +10%% or -15%%")
    parser.add_argument("--edge-pitch", default=None,
                        help="edge-tts pitch, e.g. +5Hz or -10Hz")
    parser.add_argument("--intercom", action="store_true",
                        help="apply a cabin PA / intercom effect (needs ffmpeg)")
    parser.add_argument("--no-chime", dest="chime", action="store_false",
                        help="with --intercom, skip the two-tone cabin chime")
    parser.add_argument("--crackle", action="store_true",
                        help="with --intercom, mix in radio static/crackle")
    parser.set_defaults(chime=True)
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

    if args.list_voices:
        sys.exit(0 if list_edge_voices() else 1)

    text = read_script(args.input)
    output = args.output or default_output(args.engine)

    # With --intercom we synthesize to a temp file, then post-process into output.
    raw_output = output
    if args.intercom:
        base, ext = os.path.splitext(output)
        raw_output = base + ".raw" + (ext or ".mp3")

    if args.engine == "edge":
        ok = synthesize_edge(text, raw_output, voice=args.voice,
                             rate=args.edge_rate, pitch=args.edge_pitch)
    elif args.engine == "gtts":
        ok = synthesize_gtts(text, raw_output, lang=args.lang, slow=args.slow)
    elif args.engine == "pyttsx3":
        ok = synthesize_pyttsx3(text, raw_output, rate=args.rate, volume=args.volume)
    else:  # auto: best quality first, degrade gracefully to offline
        ok = synthesize_edge(text, raw_output, voice=args.voice,
                             rate=args.edge_rate, pitch=args.edge_pitch)
        if not ok:
            print("Falling back to gTTS engine...", file=sys.stderr)
            ok = synthesize_gtts(text, raw_output, lang=args.lang, slow=args.slow)
        if not ok:
            print("Falling back to offline pyttsx3 engine...", file=sys.stderr)
            ok = synthesize_pyttsx3(text, raw_output, rate=args.rate, volume=args.volume)

    if not ok:
        sys.exit("Error: could not generate audio. Install a backend "
                 "(pip install edge-tts gTTS pyttsx3) and try again.")

    if args.intercom:
        if apply_intercom(raw_output, output, chime=args.chime, crackle=args.crackle):
            try:
                os.remove(raw_output)
            except OSError:
                pass
        else:
            output = raw_output  # effect failed; keep the clean audio
            print("Kept the un-filtered audio instead.", file=sys.stderr)

    print(f"Audio written to {output}")


if __name__ == "__main__":
    main()
