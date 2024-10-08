# -*- coding:utf-8 -*-
import os
import time
from typing import Union, List
from typing import Optional
import uvicorn
from fastapi import FastAPI, Request, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from vits_minio import TTSStore
from vits_mp3 import VitsInfer
from fastapi import File, UploadFile
import argparse
import os.path
from pathlib import Path
from starlette.responses import FileResponse

def parse_args():
    parser = argparse.ArgumentParser(description='vits server')
    parser.add_argument('--config', type=str, default='./configs/bert_vits.json')
    parser.add_argument('--model', type=str, default='logs/bert_vits/G_1760000.pth')
    parser.add_argument('-m', '--message', type=int, default=1, required=False, help='output debug message')
    parser.add_argument('-p', '--port', type=int, default=8113, required=False, help='port number')
    parser.add_argument('-w', '--workers', type=int, default=2, required=False, help='worker number')

    return parser.parse_args()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load resources
    global g_vits
    print('liftspan', 'start...')
    args = parse_args()
    g_vits = VitsInfer(args.model, args.config)
    print('liftspan', 'finish.')
    yield
    # Clean up and release resources
    pass

app = FastAPI(lifespan=lifespan)
      
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"The parameter is incorrect. {request.method} {request.url}")
    return JSONResponse({"code": "400", "message": exc.errors()})
    
class TtsModel(BaseModel):
    token:str = ''
    vcn:str = 'zh-CN-Xiaoyu'
    speed:float = 1.0
    volume:float = 1.0
    text:str

class Tts3Model(BaseModel):
    speed:float = 1.0
    volume:float = 1.0
    sen:str

@app.post("/tts")
async def tts(ttsModel: TtsModel):
    start = time.time()
    args = ttsModel.model_dump()
    filename = g_vits.infer(args['text'])
    end = time.time()

    fr = FileResponse(
        path=filename,
        filename=Path(filename).name,
    )

    print('{} {} {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), ttsModel.model_dump(), end - start))
    
    return fr

@app.post("/api_zh_blcu")
async def api_zh_blcu(ttsModel: Tts3Model):
    tts = TTSStore()
    start = time.time()
    args = ttsModel.model_dump()
    sen = args['sen']
    full_url = ''
    if tts.exist(sen):
        full_url = tts.full_url(sen)
    else:
        if tts.put(sen):
            full_url = tts.full_url(sen)
    respond = {'code':200, 'msg':'ok', 'mp3':full_url}
    end = time.time()

    print('{} {} {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), ttsModel.model_dump(), end - start))
    
    return JSONResponse(content=respond)


if __name__ == "__main__":
    args = parse_args()
    print('vits_fastapi server', 'port = {}, worker = {}.'.format(args.port, args.workers))
    uvicorn.run(app='vits_fastapi:app', host='0.0.0.0', log_level='warning', port=args.port, workers=args.workers, reload=False)
