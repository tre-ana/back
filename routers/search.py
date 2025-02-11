import urllib.parse
import urllib.request

from fastapi import APIRouter

import json
import pandas as pd

NAVER_CLIENT_ID = 'rB38ibQAfZlLMOpckjr0'
NAVER_CLIENT_SECRET = '0kJ8X9YOI3'

url = 'https://openapi.naver.com/v1/search/blog?query='

router = APIRouter()

@router.get("/search/naver/blog")
def search_naver(keyword: str):
    encText = urllib.parse.quote(keyword)
    
    request = urllib.request.Request(url + encText)
    request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
    res = urllib.request.urlopen(request)
    res_body = res.read()
    
    js = json.loads(res_body.decode('utf-8'))
    result = list()
    for j in js['items']:
        result.append((j['description'], j['postdate']))
    
    return result