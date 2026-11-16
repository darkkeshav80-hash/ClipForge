import re
import json
from typing import List, Dict, Any, Optional, Tuple
from backend.core.logger import logger
from backend.providers.adapter_registry import provider_registry

# Basic Devanagari to IAST/Hinglish Phonetic Map for zero-dependency offline fallback
DEVANAGARI_MAP = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'अं': 'an', 'अः': 'ah',
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', '्': '',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'd', 'ढ़': 'rh', 'फ़': 'f',
    '।': '.',
}

def offline_devanagari_to_hinglish(text: str) -> str:
    """Phonetic rule-based transliterator for Hindi to Hinglish without AI."""
    out = []
    i = 0
    while i < len(text):
        c = text[i]
        if c in DEVANAGARI_MAP:
            val = DEVANAGARI_MAP[c]
            # In Devanagari, consonants carry an inherent 'a' unless followed by a matra or halant
            if '\u0915' <= c <= '\u0939' and i + 1 < len(text):
                nxt = text[i + 1]
                if nxt not in ['\u093e', '\u093f', '\u0940', '\u0941', '\u0942', '\u0943', '\u0947', '\u0948', '\u094b', '\u094c', '\u094d']:
                    val += 'a'
            out.append(val)
        else:
            out.append(c)
        i += 1
    res = "".join(out)
    # Fix common artifacts
    res = re.sub(r'a+', 'a', res)
    return res

class LanguageEngine:
    """
    Multilingual Caption Processor:
    - Language Translation & Transliteration (English, Hindi Devanagari, Hinglish)
    - Word Timing Redistribution (preserves exact phrase sync when word count changes)
    - Hallucination Loop Removal (detects and suppresses repeated phrases)
    """

    @staticmethod
    def drop_repeated_phrases(words: List[Dict[str, Any]], max_consecutive: int = 3) -> List[Dict[str, Any]]:
        """Removes hallucination loops (e.g. 'nahi nahi nahi nahi...') from Whisper outputs."""
        if not words:
            return []
        cleaned: List[Dict[str, Any]] = []
        repeat_count = 0
        last_word = ""

        for w in words:
            curr_norm = re.sub(r"\W+", "", w["word"].lower())
            if curr_norm == last_word and len(curr_norm) > 1:
                repeat_count += 1
                if repeat_count < max_consecutive:
                    cleaned.append(w)
            else:
                repeat_count = 0
                last_word = curr_norm
                cleaned.append(w)
        return cleaned

    async def adapt_captions_language(
        self,
        words: List[Dict[str, Any]],
        target_lang: str, # "en", "hi", "hinglish"
        spoken_lang: str = "auto"
    ) -> Tuple[List[Dict[str, Any]], bool, str]:
        """
        Translates or transliterates word tokens to target_lang while strictly
        preserving word-level timing via proportional boundary redistribution.
        Returns: (adapted_words, is_fallback, warning_message)
        """
        if not words or target_lang in ["original", "auto", ""]:
            return words, False, ""

        # Remove repetitive loops first
        clean_words = self.drop_repeated_phrases(words)
        
        # Check if already in target script
        is_hindi_script = any('\u0900' <= c <= '\u097F' for w in clean_words for c in w.get("word", ""))
        if target_lang == "hi" and is_hindi_script:
            return clean_words, False, ""
        if target_lang == "hinglish" and not is_hindi_script and spoken_lang in ["hi", "hinglish"]:
            return clean_words, False, ""

        # Group words into short timing sentences (approx 4-8 words)
        phrases: List[Dict[str, Any]] = []
        cur_words: List[Dict[str, Any]] = []
        punct_re = re.compile(r"[.?!,।]$")

        for w in clean_words:
            cur_words.append(w)
            if punct_re.search(w["word"]) or len(cur_words) >= 6:
                phrases.append({
                    "start": cur_words[0]["start"],
                    "end": cur_words[-1]["end"],
                    "text": " ".join(cw["word"] for cw in cur_words),
                    "original_words": cur_words[:]
                })
                cur_words = []
        if cur_words:
            phrases.append({
                "start": cur_words[0]["start"],
                "end": cur_words[-1]["end"],
                "text": " ".join(cw["word"] for cw in cur_words),
                "original_words": cur_words[:]
            })

        # Try neural translation with Gemini
        provider, model = await provider_registry.get_provider_for_task("caption_generation")
        if provider and getattr(provider, "api_key", None):
            try:
                system_prompt = f"""You are an expert bilingual subtitle translator.
Target Language Mode: {target_lang.upper()}
Guidelines:
- If target is 'HINGLISH': Convert spoken Hindi to natural Roman Hindi (transliterated into English alphabet, like 'kya haal hai bhai', 'aaj hum khelne wale hain'). Keep existing English/gaming terms in English! Do NOT translate to English; transliterate the Hindi speech to Roman script!
- If target is 'HI': Translate to clean conversational Hindi in Devanagari script.
- If target is 'EN': Translate to natural, punchy, spoken English suited for viral short video subtitles.
Strict JSON format: Output an array of objects matching the input array order:
[
  {{"id": 0, "target_text": "..."}},
  {{"id": 1, "target_text": "..."}}
]"""

                batch_input = [{"id": i, "text": p["text"]} for i, p in enumerate(phrases)]
                user_prompt = f"Translate/Transliterate these subtitle phrases into {target_lang}:\n{json.dumps(batch_input, ensure_ascii=False)}"

                res_text = await provider.complete(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model=model,
                    json_mode=True,
                    max_tokens=4096
                )

                # Parse JSON
                cleaned = res_text.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]

                translated_list = json.loads(cleaned)
                trans_map = {item["id"]: item.get("target_text", "") for item in translated_list if "id" in item}

                # Build new word list with timing redistribution
                new_words: List[Dict[str, Any]] = []
                for i, p in enumerate(phrases):
                    target_sentence = trans_map.get(i, p["text"]).strip()
                    if not target_sentence:
                        target_sentence = p["text"]

                    new_tokens = target_sentence.split()
                    p_start = p["start"]
                    p_end = p["end"]
                    p_dur = max(0.2, p_end - p_start)
                    n_tok = len(new_tokens)

                    # Proportional timing redistribution inside original phrase boundary
                    w_dur = p_dur / max(1, n_tok)
                    for t_idx, token in enumerate(new_tokens):
                        w_start = round(p_start + t_idx * w_dur, 2)
                        w_end = round(p_start + (t_idx + 1) * w_dur, 2)
                        new_words.append({
                            "word": token,
                            "start": w_start,
                            "end": w_end,
                            "probability": 0.95
                        })

                logger.info(f"Successfully adapted subtitles to '{target_lang}' via Gemini ({len(new_words)} words).")
                return new_words, False, ""

            except Exception as e:
                logger.warning(f"Neural subtitle language adaptation error: {e}. Using offline fallback.")

        # Offline Fallback when no API key or network error
        if target_lang == "hinglish" and is_hindi_script:
            fallback_words = []
            for w in clean_words:
                rom = offline_devanagari_to_hinglish(w["word"])
                fallback_words.append({**w, "word": rom})
            return fallback_words, True, "Transliterated to Hinglish using offline phonetic rules."

        return clean_words, True, f"AI key required for {target_lang} translation. Displayed in original audio transcript."

language_engine = LanguageEngine()
