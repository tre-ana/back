import urllib.parse
import urllib.request

from fastapi import APIRouter
from pydantic import BaseModel

import json
import pandas as pd

NAVER_CLIENT_ID = 'rB38ibQAfZlLMOpckjr0'
NAVER_CLIENT_SECRET = '0kJ8X9YOI3'

naver_blog_url = 'https://openapi.naver.com/v1/search/blog?query='
datalab_url = "https://openapi.naver.com/v1/datalab/search"

router = APIRouter()

@router.get("/naver/blog")
def search_naver(keyword: str):
    encText = urllib.parse.quote(keyword)
    
    request = urllib.request.Request(naver_blog_url + encText)
    request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
    res = urllib.request.urlopen(request)
    res_body = res.read()
    
    js = json.loads(res_body.decode('utf-8'))
    result = list()
    for j in js['items']:
        result.append((j['description'], j['postdate']))
        
    return result


@router.get("/naver/datalab")
def search_datalab(body: dict):
    
    '''
    body_dict = {
        "startDate": startDate,
        "endDate": endDate,
        "timeUnit": timeUnit,
        "keywordGroups": DataLabRequest.loads(keywordGroups),
        "device": device,
        "gender": gender,
        "ages": json.loads(ages)
    }
    '''
    
    #body_dict={} #검색 정보를 저장할 변수
    #body_dict["startDate"] = startDate # 2020-01-01
    #body_dict["endDate"] = endDate # 2024-12-31
    #body_dict["timeUnit"] = timeUnit # day, week, month
    #body_dict["keywordGroups"] = json.loads(keywordGroups) # [{"groupName": "커피", "keywords": ["아메리카노", "카페라떼"]}]
    #body_dict['device'] = device  # mo, pc
    #body_dict['gender'] = gender  # m, f
    # body_dict["ages"] = json.loads(ages) # ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
    #1: 0∼12세, 2: 13∼18세, 3: 19∼24세, 4: 25∼29세, 
    #5: 30∼34세, 6: 35∼39세, 7: 40∼44세, 8: 45∼49세, 9: 50∼54세, 10: 55∼59세, 11: 60세 이상

    body = json.dumps(body)
    
    request = urllib.request.Request(datalab_url)
    request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
    request.add_header("Content-Type","application/json")
    
    response = urllib.request.urlopen(request, data=body.encode("utf-8"))
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read()
        response_json = json.loads(response_body)
    else:
        print("Error Code:" + rescode)
    
    return response_json