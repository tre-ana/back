import os
import torch
import gdown
import torch.nn as nn
import torch.nn.functional as F

import numpy as np

import gluonnlp as nlp

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from transformers import BertModel
from kobert_tokenizer import KoBERTTokenizer
#from database import get_db
#from sqlalchemy.orm import Session

# 라우터 설정
router = APIRouter()

# KoBERT 토크나이저 및 모델 로드
tokenizer = KoBERTTokenizer.from_pretrained('skt/kobert-base-v1')
bert_model = BertModel.from_pretrained('skt/kobert-base-v1', return_dict=False)
vocab = vocab = nlp.vocab.BERTVocab.from_sentencepiece(tokenizer.vocab_file, padding_token='[PAD]')

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class BERTSentenceTransform:
    r"""BERT style data transformation.

    Parameters
    ----------
    tokenizer : BERTTokenizer.
        Tokenizer for the sentences.
    max_seq_length : int.
        Maximum sequence length of the sentences.
    pad : bool, default True
        Whether to pad the sentences to maximum length.
    pair : bool, default True
        Whether to transform sentences or sentence pairs.
    """

    def __init__(self, tokenizer, max_seq_length,vocab, pad=True, pair=True):
        self._tokenizer = tokenizer
        self._max_seq_length = max_seq_length
        self._pad = pad
        self._pair = pair
        self._vocab = vocab

    def __call__(self, line):
        """Perform transformation for sequence pairs or single sequences.

        The transformation is processed in the following steps:
        - tokenize the input sequences
        - insert [CLS], [SEP] as necessary
        - generate type ids to indicate whether a token belongs to the first
        sequence or the second sequence.
        - generate valid length

        For sequence pairs, the input is a tuple of 2 strings:
        text_a, text_b.

        Inputs:
            text_a: 'is this jacksonville ?'
            text_b: 'no it is not'
        Tokenization:
            text_a: 'is this jack ##son ##ville ?'
            text_b: 'no it is not .'
        Processed:
            tokens: '[CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]'
            type_ids: 0     0  0    0    0     0       0 0     1  1  1  1   1 1
            valid_length: 14

        For single sequences, the input is a tuple of single string:
        text_a.

        Inputs:
            text_a: 'the dog is hairy .'
        Tokenization:
            text_a: 'the dog is hairy .'
        Processed:
            text_a: '[CLS] the dog is hairy . [SEP]'
            type_ids: 0     0   0   0  0     0 0
            valid_length: 7

        Parameters
        ----------
        line: tuple of str
            Input strings. For sequence pairs, the input is a tuple of 2 strings:
            (text_a, text_b). For single sequences, the input is a tuple of single
            string: (text_a,).

        Returns
        -------
        np.array: input token ids in 'int32', shape (batch_size, seq_length)
        np.array: valid length in 'int32', shape (batch_size,)
        np.array: input token type ids in 'int32', shape (batch_size, seq_length)

        """

        # convert to unicode
        text_a = line[0]
        if self._pair:
            assert len(line) == 2
            text_b = line[1]

        tokens_a = self._tokenizer.tokenize(text_a)
        tokens_b = None

        if self._pair:
            tokens_b = self._tokenizer(text_b)

        if tokens_b:
            # Modifies `tokens_a` and `tokens_b` in place so that the total
            # length is less than the specified length.
            # Account for [CLS], [SEP], [SEP] with "- 3"
            self._truncate_seq_pair(tokens_a, tokens_b,
                                    self._max_seq_length - 3)
        else:
            # Account for [CLS] and [SEP] with "- 2"
            if len(tokens_a) > self._max_seq_length - 2:
                tokens_a = tokens_a[0:(self._max_seq_length - 2)]

        # The embedding vectors for `type=0` and `type=1` were learned during
        # pre-training and are added to the wordpiece embedding vector
        # (and position vector). This is not *strictly* necessary since
        # the [SEP] token unambiguously separates the sequences, but it makes
        # it easier for the model to learn the concept of sequences.

        # For classification tasks, the first vector (corresponding to [CLS]) is
        # used as as the "sentence vector". Note that this only makes sense because
        # the entire model is fine-tuned.
        #vocab = self._tokenizer.vocab
        vocab = self._vocab
        tokens = []
        tokens.append(vocab.cls_token)
        tokens.extend(tokens_a)
        tokens.append(vocab.sep_token)
        segment_ids = [0] * len(tokens)

        if tokens_b:
            tokens.extend(tokens_b)
            tokens.append(vocab.sep_token)
            segment_ids.extend([1] * (len(tokens) - len(segment_ids)))

        input_ids = self._tokenizer.convert_tokens_to_ids(tokens)

        # The valid length of sentences. Only real  tokens are attended to.
        valid_length = len(input_ids)

        if self._pad:
            # Zero-pad up to the sequence length.
            padding_length = self._max_seq_length - valid_length
            # use padding tokens for the rest
            input_ids.extend([vocab[vocab.padding_token]] * padding_length)
            segment_ids.extend([0] * padding_length)

        return np.array(input_ids, dtype='int32'), np.array(valid_length, dtype='int32'),\
            np.array(segment_ids, dtype='int32')


# 분류 모델 정의
class BERTClassifier(nn.Module):
    def __init__(self, bert, hidden_size=768, num_classes=8, dr_rate=0.5):
        super(BERTClassifier, self).__init__()
        self.bert = bert
        self.dropout = nn.Dropout(p=dr_rate) if dr_rate else None
        self.classifier = nn.Linear(hidden_size, num_classes)

    def gen_attention_mask(self, token_ids, valid_length):
        """유효한 토큰에 대한 attention mask 생성"""
        attention_mask = torch.zeros_like(token_ids)
        for i, v in enumerate(valid_length):
            attention_mask[i][:v] = 1
        return attention_mask.float()

    def forward(self, token_ids, valid_length, segment_ids):
        attention_mask = self.gen_attention_mask(token_ids, valid_length).to(token_ids.device)
        _, pooled_output = self.bert(input_ids=token_ids, token_type_ids=segment_ids.long(), attention_mask=attention_mask)
        
        if self.dropout:
            pooled_output = self.dropout(pooled_output)
        
        return self.classifier(pooled_output)


# 모델 다운로드 및 로드
def download_model_from_google_drive(file_id, output_path):
    """Google Drive에서 모델 다운로드"""
    url = f"https://drive.google.com/uc?id={file_id}"
    gdown.download(url, output_path, quiet=False)
    
    
def initialize_model_and_save(model_path="model.pt"):
    global model
    model = BERTClassifier(bert_model, dr_rate=0.5).to(device)
    print("Model initialized.")

    # 모델 저장
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")
    

def load_model(model_path="model.pt"):
    """모델을 로드하고 전역 변수에 할당"""
    global model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 모델 파일이 없으면 다운로드
    if not os.path.exists(model_path):
        print(f"{model_path} not found. Downloading from Google Drive...")
        download_model_from_google_drive(file_id="19RWkGe6o_FOGY3ivkwy43PbNM6zpCmkc", output_path=model_path)

    # 모델 초기화 및 state_dict 로드
    model = BERTClassifier(bert_model, dr_rate=0.5).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print("Model loaded successfully.")

# 모델 분석 API
@router.post("/analysis/sentiment")
def analyze_sentiment(sentence: str):
    """입력 문장에 대한 감정 분석 수행"""
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Model is not loaded properly.")

        labels = {0: "긍정", 1: "부정", 2: "중립"}
        predicted_label = -1
        probabilities = list()
        
        inputs = tokenizer(sentence, return_tensors="pt", padding=True, truncation=True, max_length=128)
        token_ids = inputs["input_ids"].to(device)
        segment_ids = inputs["token_type_ids"].to(device)
        valid_length = torch.tensor([token_ids.shape[1]], dtype=torch.long).to(device)  # 길이 정보

        # 모델 예측
        with torch.no_grad():
            out = model(token_ids, valid_length, segment_ids)
            
        logits = out[0].squeeze(0).detach().cpu()
        predicted_label = labels[torch.argmax(logits).item()]
        probabilities = F.softmax(logits, dim=-1).tolist()
        
        return {
            "analysis_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "predicted_class_label": predicted_label,
            "Positive": probabilities[0],
            "Negative": probabilities[1],
            "Neutral": probabilities[2],
        }


    except Exception as e:
        print(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 디버깅용 모델 정보 출력 함수
def debug_model_parameters(model):
    print("\n--- Model Parameters ---")
    for name, param in model.named_parameters():
        print(f"{name}: {param.shape}, Requires Grad: {param.requires_grad}")
    print("\n--- Model State Dict ---")
    for key, value in model.state_dict().items():
        print(f"{key}: {value.shape}")
