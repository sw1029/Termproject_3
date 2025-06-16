"""Utility script to classify question JSON files and save results.

This script is intended to be run inside ``classifier.ipynb`` or standalone.
It loads every ``*.json`` file from ``question/`` (excluding ``processed/``),
performs classification and writes the result to ``answer/``.
"""

from __future__ import annotations

import json
import glob
import shutil
from datetime import datetime
from pathlib import Path

# Dummy classifier for demonstration. Replace with actual model in the notebook.
def dummy_classify(text: str) -> str:
    if "안녕" in text or "하이" in text:
        return "인사"
    elif "날씨" in text or "더워" in text:
        return "날씨"
    elif "정보" in text or "알려줘" in text:
        return "정보"
    else:
        return "기타"

QUESTION_DIR = Path('question')
ANSWER_DIR = Path('answer')
PROCESSED_DIR = QUESTION_DIR / 'processed'

QUESTION_DIR.mkdir(exist_ok=True)
ANSWER_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

def run_classification() -> None:
    files = glob.glob(str(QUESTION_DIR / '*.json'))
    if not files:
        print('No new questions found.')
        return

    for path in files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            qid = data['question_id']
            text = data['text']
            print(f'Processing {qid}: {text}')
            label = dummy_classify(text)

            answer_id = qid.replace('q_', 'a_')
            answer_data = {
                'question_id': qid,
                'original_question': text,
                'label': label,
                'classified_at': datetime.now().isoformat(),
            }
            with open(ANSWER_DIR / f'{answer_id}.json', 'w', encoding='utf-8') as f:
                json.dump(answer_data, f, ensure_ascii=False, indent=4)
            shutil.move(path, PROCESSED_DIR / Path(path).name)
        except Exception as e:
            print(f'Failed to process {path}: {e}')

if __name__ == '__main__':
    run_classification()
