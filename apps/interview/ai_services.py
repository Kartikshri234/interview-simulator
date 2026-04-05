"""
AI Service Layer
Handles: OpenAI question generation, answer evaluation,
         Speech-to-Text, Sentiment Analysis, DeepFace emotion detection,
         Voice analytics (Feature 15).
"""
import os
import random
import logging
import base64

from textblob import TextBlob
from django.conf import settings

logger = logging.getLogger(__name__)

# DeepFace is optional and expensive to import (TensorFlow init), so keep it lazy.
DeepFace = None
DEEPFACE_AVAILABLE = None


def _get_deepface():
    """Import DeepFace on first use to avoid slow Django startup."""
    global DeepFace, DEEPFACE_AVAILABLE
    if DEEPFACE_AVAILABLE is not None:
        return DeepFace, DEEPFACE_AVAILABLE
    try:
        from deepface import DeepFace as _DeepFace
        DeepFace = _DeepFace
        DEEPFACE_AVAILABLE = True
    except Exception:
        DeepFace = None
        DEEPFACE_AVAILABLE = False
    return DeepFace, DEEPFACE_AVAILABLE


# ── 1. QUESTION GENERATION ────────────────────────────────────

def generate_questions(category: str, difficulty: str, count: int) -> list:
    """Generate questions via OpenAI, fall back to built-in bank."""
    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            import json
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = (
                f"Generate {count} {difficulty}-level technical interview questions "
                f"for the topic: {category}. "
                "Return a JSON object with key 'questions', an array where each item has: "
                "question_text (string), expected_keywords (list of 4-6 strings), "
                "ideal_answer_outline (string), time_limit_seconds (integer)."
            )
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': 'You are an expert technical interviewer. Return only valid JSON.'},
                    {'role': 'user',   'content': prompt},
                ],
                response_format={'type': 'json_object'},
                max_tokens=2000,
            )
            data = json.loads(resp.choices[0].message.content)
            qs   = data.get('questions', [])
            if qs:
                return qs[:count]
        except Exception as e:
            logger.warning(f'OpenAI question generation failed: {e}')
    return _static_questions(category, difficulty, count)


def _static_questions(category, difficulty, count):
    bank = {
        'python': [
            {'question_text': 'Explain the difference between a list, tuple, and set in Python.',
             'expected_keywords': ['mutable', 'immutable', 'hashable', 'ordered', 'unique'],
             'ideal_answer_outline': 'Discuss mutability, ordering, and use-cases for each.',
             'time_limit_seconds': 90},
            {'question_text': 'What is the Python GIL and how does it affect multi-threading?',
             'expected_keywords': ['GIL', 'CPython', 'thread', 'multiprocessing', 'concurrency'],
             'ideal_answer_outline': 'Explain what GIL is, its purpose, and workarounds.',
             'time_limit_seconds': 120},
            {'question_text': 'How do decorators work in Python? Write an example.',
             'expected_keywords': ['decorator', 'wrapper', 'functools', 'closure', '@'],
             'ideal_answer_outline': 'Explain concept, write a timing or logging decorator.',
             'time_limit_seconds': 120},
            {'question_text': 'Explain generators and the yield keyword.',
             'expected_keywords': ['yield', 'generator', 'lazy', 'iterator', 'memory'],
             'ideal_answer_outline': 'Lazy evaluation, memory efficiency, send() method.',
             'time_limit_seconds': 90},
            {'question_text': 'What are Python context managers and how do you create one?',
             'expected_keywords': ['with', '__enter__', '__exit__', 'contextlib', 'resource'],
             'ideal_answer_outline': 'Protocol, use-cases, class-based vs contextlib.',
             'time_limit_seconds': 100},
            {'question_text': 'Explain list comprehensions vs generator expressions.',
             'expected_keywords': ['comprehension', 'generator', 'memory', 'lazy', 'iterable'],
             'ideal_answer_outline': 'Syntax differences, when to use each, memory implications.',
             'time_limit_seconds': 90},
        ],
        'django': [
            {'question_text': 'Explain Django\'s MTV architecture.',
             'expected_keywords': ['model', 'template', 'view', 'ORM', 'request', 'response'],
             'ideal_answer_outline': 'Model=data, Template=presentation, View=logic.',
             'time_limit_seconds': 90},
            {'question_text': 'How do you optimise Django ORM queries to avoid the N+1 problem?',
             'expected_keywords': ['select_related', 'prefetch_related', 'N+1', 'queryset', 'JOIN'],
             'ideal_answer_outline': 'Explain N+1, select_related for FK, prefetch_related for M2M.',
             'time_limit_seconds': 120},
            {'question_text': 'What is Django middleware and how does it work?',
             'expected_keywords': ['middleware', 'request', 'response', 'process_view', 'hook'],
             'ideal_answer_outline': 'Request/response hooks, order, writing custom middleware.',
             'time_limit_seconds': 90},
            {'question_text': 'Explain Django signals with an example.',
             'expected_keywords': ['signal', 'receiver', 'post_save', 'pre_save', 'dispatch'],
             'ideal_answer_outline': 'Observer pattern, connecting sender/receiver, use-cases.',
             'time_limit_seconds': 100},
            {'question_text': 'How do you implement authentication in a Django REST API?',
             'expected_keywords': ['JWT', 'token', 'session', 'DRF', 'permission', 'authentication'],
             'ideal_answer_outline': 'JWT vs session, DRF auth classes, permissions.',
             'time_limit_seconds': 120},
            {'question_text': 'What are Django migrations and how do they work?',
             'expected_keywords': ['migration', 'makemigrations', 'migrate', 'schema', 'database'],
             'ideal_answer_outline': 'Schema versioning, migration files, squashing.',
             'time_limit_seconds': 90},
        ],
        'dsa': [
            {'question_text': 'Explain Big O notation with examples.',
             'expected_keywords': ['O(n)', 'O(log n)', 'O(1)', 'time complexity', 'space complexity'],
             'ideal_answer_outline': 'Definition, common complexities, examples.',
             'time_limit_seconds': 120},
            {'question_text': 'How does a binary search tree work? Explain insert and search.',
             'expected_keywords': ['BST', 'left', 'right', 'root', 'search', 'insert', 'balanced'],
             'ideal_answer_outline': 'BST property, traversal, O(log n) average case.',
             'time_limit_seconds': 120},
            {'question_text': 'What is dynamic programming? Give an example.',
             'expected_keywords': ['memoization', 'tabulation', 'subproblem', 'fibonacci', 'optimal'],
             'ideal_answer_outline': 'Overlapping subproblems, optimal substructure, top-down vs bottom-up.',
             'time_limit_seconds': 150},
            {'question_text': 'Explain the difference between BFS and DFS.',
             'expected_keywords': ['BFS', 'DFS', 'queue', 'stack', 'level', 'depth', 'graph'],
             'ideal_answer_outline': 'Data structures used, use-cases, time/space complexity.',
             'time_limit_seconds': 120},
            {'question_text': 'How does a hash table work and what is collision resolution?',
             'expected_keywords': ['hash', 'bucket', 'collision', 'chaining', 'open addressing', 'O(1)'],
             'ideal_answer_outline': 'Hash function, collision strategies, load factor.',
             'time_limit_seconds': 120},
        ],
        'behavioral': [
            {'question_text': 'Tell me about a time you resolved a conflict in your team.',
             'expected_keywords': ['conflict', 'communication', 'resolution', 'team', 'listen'],
             'ideal_answer_outline': 'Use STAR: situation, task, action, result.',
             'time_limit_seconds': 150},
            {'question_text': 'Describe a project where you had to learn something new quickly.',
             'expected_keywords': ['learn', 'challenge', 'research', 'adapt', 'outcome'],
             'ideal_answer_outline': 'How you identified the gap, resources used, outcome.',
             'time_limit_seconds': 150},
            {'question_text': 'Tell me about a time you missed a deadline and what you did.',
             'expected_keywords': ['deadline', 'priority', 'communicate', 'plan', 'lesson'],
             'ideal_answer_outline': 'Honest account, steps taken, what you learned.',
             'time_limit_seconds': 150},
        ],
        'system_design': [
            {'question_text': 'Design a URL shortener like bit.ly.',
             'expected_keywords': ['hash', 'database', 'cache', 'redirect', 'scale', 'CDN'],
             'ideal_answer_outline': 'Requirements, schema, hashing strategy, caching, scaling.',
             'time_limit_seconds': 180},
            {'question_text': 'How would you design a notification system for a social app?',
             'expected_keywords': ['queue', 'pub-sub', 'websocket', 'push', 'fan-out', 'scale'],
             'ideal_answer_outline': 'Fan-out strategies, message queues, delivery guarantees.',
             'time_limit_seconds': 180},
        ],
        'database': [
            {'question_text': 'Explain the difference between SQL and NoSQL databases.',
             'expected_keywords': ['schema', 'ACID', 'CAP', 'scalability', 'relational', 'document'],
             'ideal_answer_outline': 'ACID vs BASE, use-cases, examples.',
             'time_limit_seconds': 120},
            {'question_text': 'What are database indexes and when should you use them?',
             'expected_keywords': ['index', 'B-tree', 'performance', 'read', 'write', 'query'],
             'ideal_answer_outline': 'How indexes work, types, trade-offs.',
             'time_limit_seconds': 100},
        ],
        'javascript': [
            {'question_text': 'Explain the event loop in JavaScript.',
             'expected_keywords': ['event loop', 'call stack', 'microtask', 'macrotask', 'async'],
             'ideal_answer_outline': 'Call stack, task queue, microtask queue, how async works.',
             'time_limit_seconds': 120},
            {'question_text': 'What is closure in JavaScript and when would you use it?',
             'expected_keywords': ['closure', 'scope', 'lexical', 'function', 'encapsulation'],
             'ideal_answer_outline': 'Definition, examples, module pattern, IIFE.',
             'time_limit_seconds': 90},
        ],
        'devops': [
            {'question_text': 'What is Docker and how does it differ from a VM?',
             'expected_keywords': ['container', 'image', 'VM', 'kernel', 'isolation', 'Dockerfile'],
             'ideal_answer_outline': 'Containers vs VMs, Docker concepts, use-cases.',
             'time_limit_seconds': 120},
            {'question_text': 'Explain CI/CD and its benefits.',
             'expected_keywords': ['CI', 'CD', 'pipeline', 'test', 'deploy', 'automation'],
             'ideal_answer_outline': 'Continuous integration, delivery, deployment stages.',
             'time_limit_seconds': 100},
        ],
        'ml': [
            {'question_text': 'Explain the difference between overfitting and underfitting.',
             'expected_keywords': ['overfitting', 'underfitting', 'bias', 'variance', 'regularisation'],
             'ideal_answer_outline': 'Bias-variance tradeoff, techniques to address each.',
             'time_limit_seconds': 120},
            {'question_text': 'What is gradient descent and how does it work?',
             'expected_keywords': ['gradient', 'learning rate', 'loss', 'optimiser', 'backpropagation'],
             'ideal_answer_outline': 'Objective function, derivative, step size, variants.',
             'time_limit_seconds': 120},
        ],
    }
    pool = bank.get(category, bank['python'])
    random.shuffle(pool)
    return pool[:count]


# ── 2. ANSWER EVALUATION ──────────────────────────────────────

def evaluate_answer(question_text: str, answer_text: str, expected_keywords: list) -> dict:
    """Evaluate answer with OpenAI; fall back to heuristic scoring."""
    if settings.OPENAI_API_KEY and answer_text.strip():
        try:
            from openai import OpenAI
            import json
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = f"""Evaluate this technical interview answer.

Question: {question_text}
Expected Keywords: {', '.join(expected_keywords)}
Candidate Answer: {answer_text}

Return JSON with these exact keys:
- score: float 0-10
- confidence_score: float 0-10 (confidence of delivery based on language)
- keywords_matched: list of keywords from the expected list that were addressed
- ai_feedback: 2-3 sentences of constructive feedback
- improvement_suggestions: 2-3 bullet points as a single string
- strengths: list of 2 things done well
"""
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': 'You are an expert technical interviewer. Return only valid JSON.'},
                    {'role': 'user',   'content': prompt},
                ],
                response_format={'type': 'json_object'},
                max_tokens=600,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            logger.warning(f'OpenAI evaluation failed: {e}')
    return _heuristic_eval(answer_text, expected_keywords)


def _heuristic_eval(answer_text: str, expected_keywords: list) -> dict:
    lower   = answer_text.lower()
    matched = [kw for kw in expected_keywords if kw.lower() in lower]
    ratio   = len(matched) / max(len(expected_keywords), 1)
    score   = round(3.0 + ratio * 7.0, 1)
    words   = len(answer_text.split())
    conf    = min(10.0, round(4 + (words / 50), 1))
    return {
        'score':                  score,
        'confidence_score':       conf,
        'keywords_matched':       matched,
        'ai_feedback':            f'Your answer covered {len(matched)}/{len(expected_keywords)} key topics. Try to be more specific with examples.',
        'improvement_suggestions': '• Use concrete examples\n• Mention edge cases\n• Structure your answer clearly',
        'strengths':              ['Attempted the question', 'Showed understanding of the topic'],
    }


# ── 3. SPEECH TO TEXT ─────────────────────────────────────────

def transcribe_audio(file_path: str) -> str:
    """Convert audio file to text using Google Speech Recognition."""
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            r.adjust_for_ambient_noise(source, duration=0.3)
            audio = r.record(source)
        return r.recognize_google(audio)
    except Exception as e:
        logger.warning(f'Transcription failed: {e}')
        return ''


# ── 4. SENTIMENT ANALYSIS ─────────────────────────────────────

def analyze_sentiment(text: str) -> dict:
    """Analyse sentiment using TextBlob."""
    if not text.strip():
        return {'sentiment': 'neutral', 'score': 0.0, 'confidence_score': 5.0}
    blob      = TextBlob(text)
    polarity  = blob.sentiment.polarity
    label     = 'positive' if polarity > 0.1 else ('negative' if polarity < -0.1 else 'neutral')
    conf      = round((polarity + 1) / 2 * 10, 1)
    return {'sentiment': label, 'score': round(polarity, 3), 'confidence_score': conf}


# ── 5. FACIAL EXPRESSION ANALYSIS ────────────────────────────

def analyze_face_base64(image_b64: str) -> dict:
    """Run DeepFace on a base64-encoded image.
    Falls back gracefully if DeepFace/TensorFlow is not available (e.g. Render free tier).
    """
    deepface_cls, deepface_available = _get_deepface()
    if not deepface_available:
        logger.info('DeepFace not available — returning neutral emotion.')
        return {'dominant_emotion': 'neutral', 'emotions': {'neutral': 100.0}}
    try:
        import cv2, numpy as np, tempfile
        img_bytes = base64.b64decode(image_b64)
        nparr     = np.frombuffer(img_bytes, np.uint8)
        img       = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            cv2.imwrite(tmp.name, img)
            result = deepface_cls.analyze(tmp.name, actions=['emotion'],
                                          enforce_detection=False, silent=True)
        if isinstance(result, list):
            result = result[0]
        emotions  = result.get('emotion', {})
        dominant  = result.get('dominant_emotion', 'neutral')
        return {'dominant_emotion': dominant,
                'emotions': {k: round(v, 1) for k, v in emotions.items()}}
    except Exception as e:
        logger.warning(f'DeepFace failed: {e}')
        return {'dominant_emotion': 'neutral', 'emotions': {'neutral': 100.0}}


# ── 6. SESSION SUMMARY ────────────────────────────────────────

def generate_summary(session_data: dict) -> dict:
    """Generate overall session feedback via OpenAI."""
    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            import json
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = f"""Based on this interview session data, create a performance summary.

{json.dumps(session_data, indent=2)}

Return JSON with:
- overall_feedback: 3-4 sentence summary paragraph
- strengths: list of 3 key strengths shown
- improvement_areas: list of 3 areas to work on
- recommended_topics: list of 3 topics to study
- readiness: one of "Not Ready", "Almost Ready", "Ready", "Excellent"
"""
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': 'You are a career coach. Return only valid JSON.'},
                    {'role': 'user',   'content': prompt},
                ],
                response_format={'type': 'json_object'},
                max_tokens=700,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            logger.warning(f'Summary generation failed: {e}')
    avg = session_data.get('average_score', 5)
    return {
        'overall_feedback':   f'You completed the interview with an average score of {avg}/10. Keep practising to improve your technical depth.',
        'strengths':          ['Completed all questions', 'Showed consistent effort', 'Engaged with every topic'],
        'improvement_areas':  ['Add more concrete code examples', 'Deepen system design knowledge', 'Practice explaining concepts aloud'],
        'recommended_topics': ['LeetCode DSA patterns', 'System Design Primer', 'Django advanced docs'],
        'readiness':          'Ready' if avg >= 7 else ('Almost Ready' if avg >= 5 else 'Not Ready'),
    }


# ── 7. VOICE ANALYTICS (Feature 15) ──────────────────────────

FILLER_WORDS = [
    'um', 'uh', 'like', 'you know', 'basically', 'literally',
    'actually', 'right', 'so', 'well', 'kind of', 'sort of',
]


def analyze_voice(text: str, time_taken_seconds: int = 60) -> dict:
    """
    Feature 15: Analyse spoken/typed answer for speech rate and filler words.
    Works on transcribed text. time_taken_seconds defaults to 60s if not provided.
    Returns: wpm, word_count, filler_count, filler_words list.
    """
    if not text or not text.strip():
        return {'wpm': 0, 'filler_count': 0, 'filler_words': [], 'word_count': 0}

    words      = text.split()
    word_count = len(words)
    minutes    = max(time_taken_seconds / 60, 0.1)
    wpm        = round(word_count / minutes)

    lower = text.lower()
    found_fillers = []
    for filler in FILLER_WORDS:
        import re
        pattern = r'\b' + re.escape(filler) + r'\b'
        matches = re.findall(pattern, lower)
        if matches:
            found_fillers.append({'word': filler, 'count': len(matches)})

    total_fillers = sum(f['count'] for f in found_fillers)
    return {
        'wpm':          wpm,
        'word_count':   word_count,
        'filler_count': total_fillers,
        'filler_words': found_fillers,
    }
