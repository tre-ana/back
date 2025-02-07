import os
import torch
import gdown
import torch.nn as nn
import torch.nn.functional as F

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from transformers import BertModel
from kobert_tokenizer import KoBERTTokenizer
#from database import get_db
from sqlalchemy.orm import Session

# 라우터 설정
router = APIRouter()

# KoBERT 토크나이저 및 모델 로드
tokenizer = KoBERTTokenizer.from_pretrained('skt/kobert-base-v1')
bert_model = BertModel.from_pretrained('skt/kobert-base-v1', return_dict=False)

# 분류 모델 정의
class BERTClassifier(nn.Module):
    def __init__(self, bert, hidden_size=768, num_classes=3, dr_rate=0.5):
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
        download_model_from_google_drive(file_id="1t2PPNGawil9dcqFbUie5JJL-02_FDD0y", output_path=model_path)

    # 모델 초기화 및 state_dict 로드
    model = BERTClassifier(bert_model, dr_rate=0.5).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print("Model loaded successfully.")

# 모델 분석 API
@router.post("/analysis/sentiment")
async def analyze_sentiment(sentence: str):
    """입력 문장에 대한 감정 분석 수행"""
    try:
        if model is None:
            raise HTTPException(status_code=500, detail="Model is not loaded properly.")

        # 문장 토큰화 및 텐서 변환
        inputs = tokenizer.batch_encode_plus([sentence], return_tensors="pt", padding=True, truncation=True, max_length=128)
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]
        segment_ids = torch.zeros_like(input_ids)  # KoBERT에서는 segment_ids 사용

        # 모델 예측
        with torch.no_grad():
            logits = model(input_ids, torch.tensor([len(input_ids[0])]), segment_ids)
            probabilities = F.softmax(logits, dim=1).squeeze(0).tolist()

        # 결과 매핑
        labels = {0: "긍정", 1: "부정", 2: "중립"}
        predicted_label = labels[torch.argmax(logits).item()]

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

# FastAPI 실행 시 모델 로드
try:
    load_model("model.pt")
except Exception as e:
    print(f"Error during model setup: {e}")

# 디버깅용 모델 정보 출력 함수
def debug_model_parameters(model):
    print("\n--- Model Parameters ---")
    for name, param in model.named_parameters():
        print(f"{name}: {param.shape}, Requires Grad: {param.requires_grad}")
    print("\n--- Model State Dict ---")
    for key, value in model.state_dict().items():
        print(f"{key}: {value.shape}")
