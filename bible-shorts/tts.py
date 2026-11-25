#!/usr/bin/env python3
"""Google Cloud TTS (REST) -> voice.mp3.  Usage: GOOGLE_TTS_API_KEY=... python3 tts.py [script.txt] [voice.mp3]"""
import os, sys, json, base64, urllib.request
key = os.environ["GOOGLE_TTS_API_KEY"]
src = sys.argv[1] if len(sys.argv) > 1 else "script.txt"
out = sys.argv[2] if len(sys.argv) > 2 else "voice.mp3"
text = " ... ".join(l.strip() for l in open(src, encoding="utf-8") if l.strip())
body = {
    "input": {"text": text},
    # Journey voices don't support pitch; use Studio-Q / Neural2-D if you need pitch.
    "voice": {"languageCode": "en-US", "name": os.environ.get("TTS_VOICE", "en-US-Studio-Q")},
    "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.92, "pitch": -2.0},
}
req = urllib.request.Request(
    f"https://texttospeech.googleapis.com/v1/text:synthesize?key={key}",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
audio = json.load(urllib.request.urlopen(req))["audioContent"]
open(out, "wb").write(base64.b64decode(audio))
print("saved", out)
