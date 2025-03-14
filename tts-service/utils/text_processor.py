import re
import logging
from typing import List, Dict, Any, Optional
import nltk
from nltk.tokenize import sent_tokenize

# Tải các model cần thiết cho NLTK (nếu cần)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

logger = logging.getLogger(__name__)


def preprocess_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)

    # Chuẩn hóa dấu câu
    text = re.sub(r'\s+([.,;:!?)])', r'\1', text)  # Loại bỏ khoảng trắng trước dấu câu
    text = re.sub(r'([({[])(\s+)', r'\1', text)  # Loại bỏ khoảng trắng sau dấu ngoặc mở

    # Chuẩn hóa dòng mới
    text = re.sub(r'\n+', '\n', text)

    # Thêm dấu chấm vào các câu không có dấu kết thúc
    text = add_missing_periods(text)

    # Thay thế một số ký tự đặc biệt
    text = text.replace('&', ' và ')
    text = text.replace('%', ' phần trăm ')

    # Chuẩn hóa số
    text = normalize_numbers(text)

    # Chuẩn hóa trích dẫn
    text = re.sub(r'"([^"]*)"', r'"\1"', text)

    return text.strip()


def add_missing_periods(text: str) -> str:
    lines = text.split('\n')
    processed_lines = []

    for line in lines:
        line = line.strip()
        if line and not line[-1] in ['.', '!', '?', ':', ';', ',', ')', ']', '}']:
            line += '.'
        processed_lines.append(line)

    return '\n'.join(processed_lines)


def normalize_numbers(text: str) -> str:
    # Chuẩn hóa số thập phân
    text = re.sub(r'(\d+)\.(\d+)', r'\1 phẩy \2', text)

    # Chuẩn hóa phân cách hàng nghìn
    def replace_thousands(match):
        return match.group(1).replace(',', ' ')

    text = re.sub(r'(\d{1,3}(,\d{3})+)', replace_thousands, text)

    return text


def split_text_into_chunks(text: str, chunk_size: Optional[int] = None) -> List[Dict[str, Any]]:
    if not chunk_size:
        from core.config import settings
        chunk_size = settings.CHUNK_SIZE

    chunks = []
    paragraphs = text.split('\n')

    current_chunk = ""
    current_start = 0

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current_chunk:
                chunks.append({
                    "start_index": current_start,
                    "end_index": current_start + len(current_chunk),
                    "text": current_chunk
                })
                current_chunk = ""

            sentences = sent_tokenize(paragraph)

            temp_chunk = ""
            temp_start = current_start

            for sentence in sentences:
                if len(temp_chunk) + len(sentence) + 1 <= chunk_size:
                    if temp_chunk:
                        temp_chunk += " "
                    temp_chunk += sentence
                else:
                    if temp_chunk:
                        chunks.append({
                            "start_index": temp_start,
                            "end_index": temp_start + len(temp_chunk),
                            "text": temp_chunk
                        })
                    temp_chunk = sentence
                    temp_start = current_start + (paragraph.find(sentence,
                                                                 temp_start - current_start) if temp_start > current_start else paragraph.find(
                        sentence))

            if temp_chunk:
                chunks.append({
                    "start_index": temp_start,
                    "end_index": temp_start + len(temp_chunk),
                    "text": temp_chunk
                })

            current_start += len(paragraph) + 1
        else:
            if current_chunk and len(current_chunk) + len(paragraph) + 1 > chunk_size:
                chunks.append({
                    "start_index": current_start,
                    "end_index": current_start + len(current_chunk),
                    "text": current_chunk
                })
                current_chunk = paragraph
                current_start = current_start + len(current_chunk) + 1
            else:
                if current_chunk:
                    current_chunk += "\n"
                current_chunk += paragraph
                if not current_chunk:
                    current_start = current_start + 1
    if current_chunk:
        chunks.append({
            "start_index": current_start,
            "end_index": current_start + len(current_chunk),
            "text": current_chunk
        })

    return chunks


def analyze_vietnamese_text(text: str) -> List[Dict[str, Any]]:
    segments = []

    paragraphs = text.split('\n')

    current_position = 0

    for paragraph in paragraphs:
        if not paragraph.strip():
            current_position += 1
            continue

        sentences = split_into_sentences_vi(paragraph)

        temp_segment = ""
        temp_start = current_position

        for sentence in sentences:

            if len(sentence) > 200:
                sub_parts = split_long_sentence_vi(sentence)

                for part in sub_parts:

                    part_start = current_position + paragraph.find(
                        part,
                       temp_start - current_position
                    ) if temp_start > current_position else current_position + paragraph.find( part)

                    segments.append({
                        "start_index": part_start,
                        "end_index": part_start + len(part),
                        "text": part
                    })
            else:
                sentence_start = current_position + paragraph.find(
                    sentence,
                    temp_start - current_position
                ) if temp_start > current_position else current_position + paragraph.find(sentence)

                segments.append({
                    "start_index": sentence_start,
                    "end_index": sentence_start + len(sentence),
                    "text": sentence
                })

            temp_start = current_position + paragraph.find(sentence) + len(sentence)

        current_position += len(paragraph) + 1

    return segments


def split_into_sentences_vi(text: str) -> List[str]:

    text = text.replace('TS.', 'TS_PLACEHOLDER')
    text = text.replace('ThS.', 'THS_PLACEHOLDER')
    text = text.replace('PGS.', 'PGS_PLACEHOLDER')
    text = text.replace('GS.', 'GS_PLACEHOLDER')
    text = text.replace('T.S.', 'TS_PLACEHOLDER')
    text = text.replace('Th.S.', 'THS_PLACEHOLDER')

    sentences = re.split(r'(?<=[.!?:])\s+', text)

    result = []
    for sentence in sentences:
        sentence = sentence.replace('TS_PLACEHOLDER', 'TS.')
        sentence = sentence.replace('THS_PLACEHOLDER', 'ThS.')
        sentence = sentence.replace('PGS_PLACEHOLDER', 'PGS.')
        sentence = sentence.replace('GS_PLACEHOLDER', 'GS.')
        result.append(sentence)

    return result


def split_long_sentence_vi(sentence: str) -> List[str]:
    parts = re.split(
        r'(?<=[,;])\s+|(?<=\s)(nhưng|và|hoặc|vì|bởi vì|do đó|vì vậy|tuy nhiên|mặc dù|dù|nếu|trong khi|để|hay là|với)(?=\s)', sentence)

    result = []
    temp_part = ""

    for part in parts:
        if not part.strip():
            continue

        if len(temp_part) + len(part) + 1 <= 200:
            if temp_part:
                temp_part += " "
            temp_part += part
        else:
            if temp_part:
                result.append(temp_part)
            temp_part = part

    if temp_part:
        result.append(temp_part)

    return result if result else [sentence]