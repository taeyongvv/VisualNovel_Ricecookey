#!/usr/bin/env python3
"""
gen_bgm.py — 합성 앰비언트 BGM 루프(WAV)를 생성한다 (표준 라이브러리만 사용).

코드/인코더가 없으므로 ffmpeg/mp3 없이 wave 모듈로 직접 PCM을 쓴다.
부드러운 화음 패드 + 가벼운 아르페지오로 분위기별 짧은 루프를 만든다.
경량화를 위해 22050Hz 모노 16bit, ~24초 루프.
출력: assets/audio/*.wav
"""

import math
import os
import struct
import wave

SR = 22050
OUT = "assets/audio"

# 음이름 → 주파수 (A4=440)
A4 = 440.0
NOTE = {n: i for i, n in enumerate(
    ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def freq(note, octave):
    midi = (octave + 1) * 12 + NOTE[note]
    return A4 * 2 ** ((midi - 69) / 12)


def pad_tone(freqs, dur, amp=0.5):
    """여러 주파수를 합친 패드. 부드러운 어택/릴리즈 엔벌로프."""
    n = int(SR * dur)
    out = [0.0] * n
    for f in freqs:
        # 약간의 디튠 2겹으로 따뜻하게
        for df, w in ((1.0, 0.6), (1.003, 0.4)):
            ph = 0.0
            inc = 2 * math.pi * f * df / SR
            for i in range(n):
                # 배음 살짝 (1, 2배음)
                s = math.sin(ph) + 0.25 * math.sin(2 * ph)
                out[i] += s * w
                ph += inc
    # 엔벌로프 (코사인 페이드 인/아웃)
    atk = int(n * 0.25); rel = int(n * 0.4)
    for i in range(n):
        e = 1.0
        if i < atk:
            e = 0.5 - 0.5 * math.cos(math.pi * i / atk)
        elif i > n - rel:
            e = 0.5 - 0.5 * math.cos(math.pi * (n - i) / rel)
        out[i] *= e * amp / len(freqs)
    return out


def arp(freqs, dur, amp=0.22, step=0.5):
    """가벼운 아르페지오 (플럭 형태)."""
    n = int(SR * dur)
    out = [0.0] * n
    sn = int(SR * step)
    for k in range(0, n, sn):
        f = freqs[(k // sn) % len(freqs)]
        ph = 0.0; inc = 2 * math.pi * f / SR
        for i in range(sn):
            if k + i >= n:
                break
            t = i / sn
            env = math.exp(-4 * t)  # 빠른 감쇠
            out[k + i] += math.sin(ph) * env * amp
            ph += inc
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def chord(notes, octave_shift=0):
    return [freq(nm, oc + octave_shift) for nm, oc in notes]


def build_loop(progression, bar=3.0, arp_notes=None, pad_amp=0.5):
    """progression: 코드(노트리스트) 리스트. 각 코드 bar초."""
    pad = []
    for ch in progression:
        pad += pad_tone(ch, bar, amp=pad_amp)
    tracks = [pad]
    if arp_notes:
        ar = []
        for ch in progression:
            ar += arp(arp_notes(ch), bar)
        tracks.append(ar)
    return mix(*tracks)


def normalize(samples, peak=0.85):
    m = max(1e-9, max(abs(v) for v in samples))
    g = peak / m
    return [v * g for v in samples]


def write_wav(name, samples):
    samples = normalize(samples)
    path = os.path.join(OUT, f"{name}.wav")
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32767)) for s in samples)
        w.writeframes(frames)
    return path, len(samples) / SR


def main():
    os.makedirs(OUT, exist_ok=True)

    # bgm_main — 우아하고 차분한 메인 테마 (Am - F - C - G)
    main_prog = [
        chord([("A", 3), ("C", 4), ("E", 4)]),
        chord([("F", 3), ("A", 3), ("C", 4)]),
        chord([("C", 4), ("E", 4), ("G", 4)]),
        chord([("G", 3), ("B", 3), ("D", 4)]),
    ]
    main = build_loop(main_prog, bar=3.0,
                      arp_notes=lambda c: [c[0]*2, c[1]*2, c[2]*2, c[1]*2], pad_amp=0.5)

    # bgm_tense — 긴장/법정/음모 (Dm - Bb - Gm - A)
    tense_prog = [
        chord([("D", 3), ("F", 3), ("A", 3)]),
        chord([("A#", 2), ("D", 3), ("F", 3)]),
        chord([("G", 3), ("A#", 3), ("D", 4)]),
        chord([("A", 3), ("C#", 4), ("E", 4)]),
    ]
    tense = build_loop(tense_prog, bar=2.4, pad_amp=0.55)

    # bgm_romance — 따뜻한 피날레 (C - Am - F - G, maj7 아르페지오)
    rom_prog = [
        chord([("C", 4), ("E", 4), ("G", 4), ("B", 4)]),
        chord([("A", 3), ("C", 4), ("E", 4), ("G", 4)]),
        chord([("F", 3), ("A", 3), ("C", 4), ("E", 4)]),
        chord([("G", 3), ("B", 3), ("D", 4), ("F", 4)]),
    ]
    romance = build_loop(rom_prog, bar=3.0,
                         arp_notes=lambda c: [c[0], c[2], c[3], c[2]], pad_amp=0.48)

    for name, data in [("bgm_main", main), ("bgm_tense", tense), ("bgm_romance", romance)]:
        path, dur = write_wav(name, data)
        size = os.path.getsize(path) / 1024
        print(f"  {name}.wav  ({dur:.1f}s, {size:.0f} KB)")
    print("BGM 생성 완료 →", OUT + "/")


if __name__ == "__main__":
    main()
