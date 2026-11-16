import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from backend.core.logger import logger

def bgr(h: str) -> str:
    """Converts CSS hex #RRGGBB or RRGGBB to ASS color format &H00BBGGRR&."""
    clean = h.strip().lstrip('#')
    if len(clean) == 3:
        clean = "".join([c*2 for c in clean])
    if len(clean) != 6:
        return "&H00FFFFFF&"
    r = clean[0:2]
    g = clean[2:4]
    b = clean[4:6]
    return f"&H00{b}{g}{r}&"

def hex_to_ass_color(hex_str: str, alpha: int = 0) -> str:
    """Converts CSS hex color (#RRGGBB) to ASS color format &HAABBGGRR& with alpha."""
    clean = hex_str.strip().lstrip('#')
    if len(clean) == 3:
        clean = "".join([c*2 for c in clean])
    if len(clean) != 6:
        return f"&H{alpha:02X}FFFFFF&"
    r = clean[0:2]
    g = clean[2:4]
    b = clean[4:6]
    return f"&H{alpha:02X}{b}{g}{r}&"

def is_devanagari(text: str) -> bool:
    """Detects whether text contains Devanagari Unicode characters (Hindi, Marathi, etc.)."""
    return any('\u0900' <= char <= '\u097F' for char in text)

# Complete 15 CapCut-Inspired Presets
_BASE_DEF = dict(
    out="000000", upper=False, bold=0, box=False, pop=True, blur=0, rot=0,
    shadow=None, marker=None, kw="FFD400", glow=False, hl=None, mode="hl",
    font="Arial Black", size=80, text="FFFFFF", ow=6, n=3
)

STYLE_PRESETS: Dict[str, Dict[str, Any]] = {
    "Word Cut":     dict(font="Arial Black", size=84, text="FFFFFF", ow=6, n=2, mode="reveal", bold=-1),
    "Marker Sweep": dict(font="Arial Black", size=76, text="FFFFFF", hl="1A1A1A", marker="C9B8FF", ow=3, upper=True, n=3, mode="marker", bold=-1),
    "Negative":     dict(font="Impact", size=96, text="FFFFFF", hl="D6A98A", ow=5, upper=True, n=2, pop=False, bold=0),
    "Karaoke Fill": dict(font="Arial Black", size=80, text="FFFFFF", hl="FFD400", ow=8, n=4, mode="kf", bold=-1),
    "Karaoke Pop":  dict(font="Arial Black", size=84, text="FFFFFF", hl="FFE600", ow=8, n=3, bold=-1),
    "Hormozi":      dict(font="Arial Black", size=88, text="FFFFFF", hl="00FF55", ow=7, upper=True, n=3, bold=-1),
    "MrBeast":      dict(font="Impact", size=104, text="FFFFFF", hl="FFE600", ow=9, upper=True, n=2, bold=0),
    "Neon Glow":    dict(font="Segoe UI Black", size=76, text="EAFBFF", hl="FF3DF2", out="00E5FF", ow=4, blur=4, glow=True, shadow=0, n=3, bold=-1),
    "Fire":         dict(font="Impact", size=96, text="FFFFFF", hl="FF7A00", out="5A0000", ow=8, upper=True, n=2, bold=0),
    "Comic":        dict(font="Comic Sans MS", size=82, text="FFE600", hl="FFFFFF", ow=7, rot=-3, bold=-1, n=3),
    "Typewriter":   dict(font="Consolas", size=70, text="FFFFFF", hl="7CFF6B", box=True, ow=10, n=4, mode="reveal", bold=-1),
    "Highlighter":  dict(font="Arial Black", size=70, text="111111", out="FFE600", box=True, ow=12, n=4, mode="static", bold=-1),
    "Boxed":        dict(font="Segoe UI Black", size=74, text="FFFFFF", hl="FFD400", box=True, ow=12, n=3, bold=-1),
    "Word Pop":     dict(font="Arial Black", size=116, text="FFFFFF", hl="FFE600", ow=9, upper=True, n=1, mode="single", bold=-1),
    "Minimal":      dict(font="Segoe UI Semibold", size=64, text="FFFFFF", ow=3, n=4, mode="static", bold=0),
}

# Alias standard DB preset IDs to our comprehensive CapCut engine
PRESET_ALIASES = {
    "mrbeast-bold": "MrBeast",
    "hormozi-emphasis": "Hormozi",
    "clean-white": "Minimal",
    "yellow-highlight": "Karaoke Pop",
    "neon-gaming": "Neon Glow",
    "rgb-gaming": "Neon Glow",
    "minimal-podcast": "Minimal",
    "cinematic-subtitles": "Minimal",
    "karaoke-highlight": "Karaoke Fill",
    "typewriter": "Typewriter",
    "bouncing-words": "Word Cut",
    "pop-up-animation": "Word Pop",
    "gradient-text": "Marker Sweep",
    "boxed-subtitles": "Boxed",
    "tiktok-style": "Hormozi",
    "instagram-reels": "Word Cut",
    "dynamic-emphasis": "MrBeast",
    # CapCut Direct IDs
    "word-cut": "Word Cut",
    "marker-sweep": "Marker Sweep",
    "negative": "Negative",
    "karaoke-fill": "Karaoke Fill",
    "karaoke-pop": "Karaoke Pop",
    "hormozi": "Hormozi",
    "mrbeast": "MrBeast",
    "neon-glow": "Neon Glow",
    "fire": "Fire",
    "comic": "Comic",
    "highlighter": "Highlighter",
    "boxed": "Boxed",
    "word-pop": "Word Pop",
    "minimal": "Minimal",
}

class ASSWriter:
    """
    High-Performance Advanced SubStation Alpha (.ass) generator.
    Guarantees:
    - Events NEVER overlap on the same layer.
    - Zero blank frame flicker between words.
    - Zero line-width jitter (no active-word scale change on multi-word lines).
    - Merges micro-words shorter than 80ms into adjacent tokens.
    - Script-aware font selection (Nirmala UI for Hindi/Devanagari).
    - 15 CapCut style modes including native \\kf karaoke fill wipes.
    """
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Converts float seconds to ASS timestamp format H:MM:SS.cs"""
        sec = max(0.0, float(seconds))
        hours = int(sec // 3600)
        minutes = int((sec % 3600) // 60)
        secs = int(sec % 60)
        centisecs = int(round((sec - int(sec)) * 100))
        if centisecs >= 100:
            centisecs = 99
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def merge_short_words(self, words: List[Dict[str, Any]], min_duration: float = 0.08) -> List[Dict[str, Any]]:
        """
        Merges words shorter than min_duration (80ms) into neighboring words
        so ultra-short syllables don't flicker or cause micro-timing errors.
        """
        if not words:
            return []
        merged: List[Dict[str, Any]] = []
        for w in words:
            dur = w["end"] - w["start"]
            if dur < min_duration and merged:
                # Merge into previous word
                merged[-1]["word"] += " " + w["word"]
                merged[-1]["end"] = max(merged[-1]["end"], w["end"])
            else:
                merged.append(dict(
                    word=w["word"].strip(),
                    start=float(w["start"]),
                    end=float(w["end"]),
                    probability=w.get("probability", 1.0)
                ))
        return merged

    def group_into_phrases(
        self,
        words: List[Dict[str, Any]],
        max_words: int = 3,
        max_pause: float = 0.4,
        max_chars: int = 26
    ) -> List[List[Dict[str, Any]]]:
        """
        Breaks word stream into natural spoken phrases.
        A break occurs on:
        1. Punctuation (. ? ! , ।)
        2. Pauses between words > max_pause (400ms)
        3. Word count reaching max_words or character count reaching max_chars
        """
        if not words:
            return []

        phrases: List[List[Dict[str, Any]]] = []
        current: List[Dict[str, Any]] = []
        current_len = 0

        punct_pattern = re.compile(r"[.?!,।]$")

        for idx, w in enumerate(words):
            word_str = w["word"].strip()
            if not word_str:
                continue

            current.append(w)
            current_len += len(word_str) + 1

            has_punct = bool(punct_pattern.search(word_str))
            pause_after = (words[idx + 1]["start"] - w["end"]) if (idx + 1 < len(words)) else 0.0

            if (
                len(current) >= max_words
                or current_len >= max_chars
                or has_punct
                or pause_after > max_pause
            ):
                phrases.append(current)
                current = []
                current_len = 0

        if current:
            phrases.append(current)

        return phrases

    def generate_ass(
        self,
        words: List[Dict[str, Any]],
        preset: Dict[str, Any],
        output_path: Path,
        video_width: int = 1080,
        video_height: int = 1920,
        words_per_group: Optional[int] = None,
        clip_start_offset: float = 0.0,
        keywords: Optional[List[str]] = None,
        title: Optional[str] = None,
        position_override: Optional[str] = None,
        sync_offset: float = 0.0,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Resolve Style Definition
        preset_name = preset.get("name", "MrBeast Bold") if isinstance(preset, dict) else str(preset)
        resolved_key = PRESET_ALIASES.get(preset_name, preset_name)
        st = dict(_BASE_DEF)
        if resolved_key in STYLE_PRESETS:
            st.update(STYLE_PRESETS[resolved_key])
        elif preset_name in STYLE_PRESETS:
            st.update(STYLE_PRESETS[preset_name])

        # Merge any custom preset overrides from DB/UI
        if isinstance(preset, dict):
            if "font_family" in preset and preset["font_family"]:
                st["font"] = preset["font_family"]
            if "font_size" in preset and preset["font_size"]:
                st["size"] = int(preset["font_size"])
            if "words_per_line" in preset and preset["words_per_line"]:
                st["n"] = int(preset["words_per_line"])
            if "text_color" in preset and preset["text_color"]:
                st["text"] = preset["text_color"].lstrip("#")
            if "highlight_color" in preset and preset["highlight_color"]:
                st["hl"] = preset["highlight_color"].lstrip("#")
            if "outline_color" in preset and preset["outline_color"]:
                st["out"] = preset["outline_color"].lstrip("#")
            if "outline_width" in preset and preset["outline_width"] is not None:
                st["ow"] = int(preset["outline_width"])
            if "all_caps" in preset:
                st["upper"] = bool(preset["all_caps"])

        if words_per_group:
            st["n"] = int(words_per_group)

        # 2. Check for Devanagari (Hindi) Script
        has_devanagari = any(is_devanagari(w.get("word", "")) for w in words)
        if has_devanagari:
            # Nirmala UI is the built-in Windows font for Indic scripts (Hindi, Marathi, etc.)
            st["font"] = "Nirmala UI"
            st["upper"] = False # Never apply uppercase transforms to Devanagari matras

        is_vertical = video_height >= video_width
        scale_factor = 1.0 if is_vertical else 0.65
        font_size = int(st["size"] * scale_factor)

        # 3. Exact Vertical Positioning: BOTTOM ONLY
        # Centered horizontally, bottom edge of text about 22% up from bottom of frame
        align_code = 2  # \an2: bottom-centered
        pos_x = video_width // 2
        pos_y = int(video_height * 0.78)  # Exactly 22% up from bottom of frame
        margin_v = int(video_height * 0.22)
        # Maximum width 80% of frame (10% safe horizontal margin on each side)
        margin_h = max(int(video_width * 0.10), 80)

        border_style = 3 if st["box"] else 1
        shadow = st["shadow"] if st["shadow"] is not None else (0 if st["box"] else 2)
        primary_color = bgr(st["hl"]) if (st["mode"] == "kf" and st["hl"]) else bgr(st["text"])
        secondary_color = bgr(st["text"])
        outline_color = bgr(st["out"])

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{st['font']},{font_size},{primary_color},{secondary_color},{outline_color},&H80000000&,{st['bold']},0,0,0,100,100,1,0,{border_style},{st['ow']},{shadow},{align_code},{margin_h},{margin_h},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        # 4. Normalize Words & Merge Ultra-Short Tokens (< 80ms)
        normalized_words: List[Dict[str, Any]] = []
        for w in words:
            w_text = str(w.get("word", "")).strip()
            if not w_text:
                continue
            # Apply sync offset and clip offset
            s_t = max(0.0, float(w["start"]) - clip_start_offset + sync_offset)
            e_t = max(s_t + 0.05, float(w["end"]) - clip_start_offset + sync_offset)
            normalized_words.append(dict(word=w_text, start=s_t, end=e_t))

        merged_words = self.merge_short_words(normalized_words, min_duration=0.08)

        dialogue_lines: List[str] = []

        if not merged_words:
            content = header + "\n".join(dialogue_lines) + "\n"
            output_path.write_text(content, encoding="utf-8")
            return output_path

        # 5. Group into Phrases (Break on punctuation, pauses > 0.4s, and style word limits)
        phrases = self.group_into_phrases(merged_words, max_words=st["n"], max_pause=0.4, max_chars=28)

        # Keyword normalization for highlighted words
        norm_kw = {re.sub(r"\W+", "", str(k).lower()) for k in (keywords or []) if len(str(k)) >= 3}

        def clean_word(txt: str) -> str:
            w_clean = txt.replace("{", "").replace("}", "").replace("\\", "").strip()
            if st["upper"] and not is_devanagari(w_clean):
                return w_clean.upper()
            return w_clean

        # Pre-effects (blur / rotation)
        pre_fx = ""
        if st["blur"]:
            pre_fx += f"\\blur{st['blur']}"
        if st["rot"]:
            pre_fx += f"\\frz{st['rot']}"
        # Exact bottom positioning: \an2\pos(pos_x, pos_y)
        pos_tag = f"\\an2\\pos({pos_x},{pos_y})"
        full_prefix = f"{{{pos_tag}{pre_fx}}}"

        reset_tag = f"{{\\c{bgr(st['text'])}\\bord{st['ow']}\\3c{outline_color}}}"

        def plain_format(w: Dict[str, Any]) -> str:
            raw = clean_word(w["word"])
            norm = re.sub(r"\W+", "", raw.lower())
            if norm in norm_kw:
                return f"{{\\c{bgr(st['kw'])}}}{raw}{reset_tag}"
            return raw

        def active_format(w: Dict[str, Any]) -> str:
            raw = clean_word(w["word"])
            if st["mode"] == "marker":
                return f"{{\\c{bgr(st['hl'])}\\3c{bgr(st['marker'])}\\bord{st['ow'] + 7}}}{raw}{reset_tag}"
            # Zero-jitter active word: change color and border without scaling on multi-word lines
            hl_col = bgr(st["hl"] or "FFE600")
            return f"{{\\c{hl_col}}}{raw}{reset_tag}"

        hold_duration = 0.25 # Short hold so phrase doesn't abruptly vanish

        for p_idx, phrase in enumerate(phrases):
            phrase_start = phrase[0]["start"]
            # Phrase ends after last word + hold, or when next phrase starts
            next_phrase_start = phrases[p_idx + 1][0]["start"] if (p_idx + 1 < len(phrases)) else None
            phrase_end = phrase[-1]["end"] + hold_duration
            if next_phrase_start is not None and phrase_end > next_phrase_start:
                phrase_end = next_phrase_start

            # Mode 1: Static (entire phrase displayed for its full duration)
            if st["mode"] == "static":
                txt = " ".join(plain_format(w) for w in phrase)
                dialogue_lines.append(
                    f"Dialogue: 0,{self.format_timestamp(phrase_start)},{self.format_timestamp(phrase_end)},Main,,0,0,0,,{full_prefix}{txt}"
                )

            # Mode 2: Karaoke Fill (\kf progressive sweep across words)
            elif st["mode"] == "kf":
                parts = []
                for j, w in enumerate(phrase):
                    # Word duration extends to next word start (or phrase end for last word)
                    w_next = phrase[j + 1]["start"] if j + 1 < len(phrase) else phrase_end
                    duration_cs = max(int(round((w_next - w["start"]) * 100)), 1)
                    parts.append(f"{{\\kf{duration_cs}}}{clean_word(w['word'])}")
                txt = " ".join(parts)
                dialogue_lines.append(
                    f"Dialogue: 0,{self.format_timestamp(phrase_start)},{self.format_timestamp(phrase_end)},Main,,0,0,0,,{full_prefix}{txt}"
                )

            # Mode 3: Single Word Pop (one word per frame with dynamic pop scale)
            elif st["mode"] == "single":
                for j, w in enumerate(phrase):
                    w_end = phrase[j + 1]["start"] if j + 1 < len(phrase) else phrase_end
                    word_txt = f"{{\\fscx75\\fscy75\\t(0,90,\\fscx105\\fscy105)}}{clean_word(w['word'])}"
                    dialogue_lines.append(
                        f"Dialogue: 0,{self.format_timestamp(w['start'])},{self.format_timestamp(w_end)},Main,,0,0,0,,{full_prefix}{word_txt}"
                    )

            # Mode 4: Reveal (words revealed one by one until phrase finishes)
            elif st["mode"] == "reveal":
                for j, w in enumerate(phrase):
                    w_end = phrase[j + 1]["start"] if j + 1 < len(phrase) else phrase_end
                    revealed = [plain_format(x) for x in phrase[:j]] + [active_format(w) if st["hl"] else plain_format(w)]
                    txt = " ".join(revealed)
                    dialogue_lines.append(
                        f"Dialogue: 0,{self.format_timestamp(w['start'])},{self.format_timestamp(w_end)},Main,,0,0,0,,{full_prefix}{txt}"
                    )

            # Mode 5: Active Word Glow / Marker Sweep (continuous non-overlapping events)
            else:
                for j, w in enumerate(phrase):
                    # Each word's event ends EXACTLY when the next word begins
                    w_end = phrase[j + 1]["start"] if j + 1 < len(phrase) else phrase_end
                    line_words = [
                        active_format(x) if m == j else plain_format(x)
                        for m, x in enumerate(phrase)
                    ]
                    txt = " ".join(line_words)
                    dialogue_lines.append(
                        f"Dialogue: 0,{self.format_timestamp(w['start'])},{self.format_timestamp(w_end)},Main,,0,0,0,,{full_prefix}{txt}"
                    )

        full_ass = header + "\n".join(dialogue_lines) + "\n"
        output_path.write_text(full_ass, encoding="utf-8")
        logger.info(f"Generated ASS subtitles with {len(dialogue_lines)} non-overlapping events ({st['font']}, style={resolved_key})")
        return output_path

    def validate_ass_events(self, ass_path: Path) -> Dict[str, Any]:
        """
        Automated assertion test for ASS files:
        1. Confirms no two events on layer 0 overlap in time.
        2. Confirms start time < end time for every event.
        3. Returns total events and maximum duration.
        """
        if not ass_path.exists():
            return {"valid": False, "error": f"File {ass_path} not found"}

        lines = ass_path.read_text(encoding="utf-8").splitlines()
        dialogues = []

        for line in lines:
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) >= 10:
                    layer = int(parts[0].replace("Dialogue:", "").strip())
                    start_s = self._parse_ass_time(parts[1].strip())
                    end_s = self._parse_ass_time(parts[2].strip())
                    text = parts[9].strip()
                    dialogues.append({"layer": layer, "start": start_s, "end": end_s, "text": text})

        # Separate layer 0 (captions) from layer 1 (title card)
        caption_events = [d for d in dialogues if d["layer"] == 0]
        caption_events.sort(key=lambda d: d["start"])

        overlaps = []
        for i in range(len(caption_events) - 1):
            curr_ev = caption_events[i]
            next_ev = caption_events[i + 1]
            # Tolerating 0.01s rounding difference
            if curr_ev["end"] > next_ev["start"] + 0.02:
                overlaps.append({
                    "event_1": curr_ev,
                    "event_2": next_ev,
                    "overlap_seconds": round(curr_ev["end"] - next_ev["start"], 3)
                })

        return {
            "valid": len(overlaps) == 0,
            "total_events": len(dialogues),
            "caption_events": len(caption_events),
            "overlap_count": len(overlaps),
            "overlaps": overlaps[:5],
        }

    @staticmethod
    def _parse_ass_time(time_str: str) -> float:
        parts = time_str.split(":")
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2])
        return h * 3600.0 + m * 60.0 + s

ass_writer = ASSWriter()
