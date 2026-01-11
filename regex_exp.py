import pandas as pd
import re
from typing import Optional, Dict, Tuple

reddit_posts = "/Users/jangalic04/Downloads/Language_and_AI/Assignment/extrovert_introvert.csv"
df = pd.read_csv(reddit_posts)

# ----------------------------
# Load your dataset
# ----------------------------
reddit_posts = "/Users/jangalic04/Downloads/Language_and_AI/Assignment/extrovert_introvert.csv"
df = pd.read_csv(reddit_posts)

# ----------------------------
# MBTI building blocks
# ----------------------------

MBTI_TYPES = [
    "INTJ","INTP","INFJ","INFP",
    "ISTJ","ISTP","ISFJ","ISFP",
    "ENTJ","ENTP","ENFJ","ENFP",
    "ESTJ","ESTP","ESFJ","ESFP"
]

# "Token-safe" pattern for MBTI type codes, allowing ENFP-T / INTJ-A / INFJ/A
MBTI_TYPE_RE = re.compile(
    r"(?<![A-Za-z])("
    + "|".join(MBTI_TYPES)
    + r")"
    r"(?:\s*[-/]\s*[AT])?"
    r"(?![A-Za-z])",
    flags=re.IGNORECASE
)

INTROVERT_WORD_RE = re.compile(r"\bintro[\s\-]?vert(?:ed|s)?\b", re.IGNORECASE)
EXTROVERT_WORD_RE = re.compile(r"\b(?:extro|extra)[\s\-]?vert(?:ed|s)?\b", re.IGNORECASE)

MBTI_META_RE = re.compile(r"\b(mbti|myers[\s\-]?briggs)\b", re.IGNORECASE)


# ----------------------------
# Self-description patterns (explicit only)
# ----------------------------
# Each pattern returns:
#  - pattern_id (for your new dataset column)
#  - regex to match
#
# IMPORTANT: these patterns are *explicit self descriptions*, not generic mentions.

SELF_DESC_PATTERNS = [
    # 1) "I am / I'm / Im an INFJ"
    (
        "SELF_MBTYPE_I_AM",
        re.compile(
            r"\b(i\s*am|i['’]?\s*m|im)\s+(an?\s+)?"
            r"(?P<mbti>(" + "|".join(MBTI_TYPES) + r")(?:\s*[-/]\s*[AT])?)\b",
            re.IGNORECASE
        )
    ),

    # 2) "As an INFJ, ..." / "As a INFJ, ..."
    (
        "SELF_MBTYPE_AS_AN",
        re.compile(
            r"\bas\s+an?\s+"
            r"(?P<mbti>(" + "|".join(MBTI_TYPES) + r")(?:\s*[-/]\s*[AT])?)\b",
            re.IGNORECASE
        )
    ),

    # 3) "MBTI: INFJ" / "my mbti is infj"
    (
        "SELF_MBTYPE_MY_MBTI_IS",
        re.compile(
            r"\b(my\s+)?mbti\s*(?:is|:)\s*"
            r"(?P<mbti>(" + "|".join(MBTI_TYPES) + r")(?:\s*[-/]\s*[AT])?)\b",
            re.IGNORECASE
        )
    ),

    # 4) "My type is INTJ" / "type: ENFP"
    (
        "SELF_MBTYPE_TYPE_IS",
        re.compile(
            r"\b(my\s+)?type\s*(?:is|:)\s*"
            r"(?P<mbti>(" + "|".join(MBTI_TYPES) + r")(?:\s*[-/]\s*[AT])?)\b",
            re.IGNORECASE
        )
    ),

    # 5) "I am an introvert" / "I'm introverted"
    (
        "SELF_TRAIT_I_AM_INTROVERT",
        re.compile(
            r"\b(i\s*am|i['’]?\s*m|im)\s+(an?\s+)?(?P<trait>intro[\s\-]?vert(?:ed)?)\b",
            re.IGNORECASE
        )
    ),

    # 6) "I am an extrovert" / "I'm extroverted/extraverted"
    (
        "SELF_TRAIT_I_AM_EXTROVERT",
        re.compile(
            r"\b(i\s*am|i['’]?\s*m|im)\s+(an?\s+)?(?P<trait>(?:extro|extra)[\s\-]?vert(?:ed)?)\b",
            re.IGNORECASE
        )
    ),

    # 7) "introvert here" / "extrovert here" (common Reddit self-ID pattern)
    (
        "SELF_TRAIT_HERE",
        re.compile(
            r"\b(?P<trait>intro[\s\-]?vert(?:ed)?|(?:extro|extra)[\s\-]?vert(?:ed)?)\s+here\b",
            re.IGNORECASE
        )
    ),

    # 8) "I'm more of an introvert" / "I'm more extroverted than ..."
    (
        "SELF_TRAIT_MORE_OF",
        re.compile(
            r"\b(i\s*am|i['’]?\s*m|im)\s+more\s+(of\s+an?\s+)?"
            r"(?P<trait>intro[\s\-]?vert(?:ed)?|(?:extro|extra)[\s\-]?vert(?:ed)?)\b",
            re.IGNORECASE
        )
    ),
]


def detect_mbti_self_description(text: str) -> Optional[Dict[str, str]]:
    """
    Return dict with pattern info if MBTI self-description is detected, else None.
    Output keys:
      - identified_pattern
      - matched_text
      - mbti_type (optional)
    """
    if not isinstance(text, str) or not text.strip():
        return None

    for pattern_id, rx in SELF_DESC_PATTERNS:
        m = rx.search(text)
        if m:
            out = {
                "identified_pattern": pattern_id,
                "matched_text": m.group(0)
            }

            # Extract groups if present
            if "mbti" in m.groupdict() and m.group("mbti") is not None:
                out["mbti_type"] = m.group("mbti").upper().replace(" ", "")
            else:
                out["mbti_type"] = None

            return out

    return None


# ----------------------------
# Apply detection + filter dataset
# ----------------------------
df_sd = df.copy()

detected = df_sd["post"].apply(detect_mbti_self_description)

df_sd["identified_pattern"] = detected.apply(lambda x: x["identified_pattern"] if isinstance(x, dict) else None)
df_sd["matched_text"] = detected.apply(lambda x: x["matched_text"] if isinstance(x, dict) else None)
df_sd["mbti_type_detected"] = detected.apply(lambda x: x["mbti_type"] if isinstance(x, dict) else None)

# Keep only posts with explicit self-description
df_self_descriptions = df_sd[df_sd["identified_pattern"].notna()].reset_index(drop=True)

# Save
df_self_descriptions.to_csv("MBTI_self_descriptions_only.csv", index=False)

print("Total posts:", len(df))
print("Self-description MBTI posts:", len(df_self_descriptions))

df_self_descriptions.to_parquet("MBTI_self_descriptions_only.parquet", index=False)
df = pd.read_parquet("MBTI_self_descriptions_only.parquet")

df.head(10).to_csv("MBTI_self_descriptions_only_sample.csv", index=False)
