from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import io
import shutil
import os
from zipfile import ZipFile

from fastapi import APIRouter
from fastapi import FastAPI, File, UploadFile
from typing import Union
from pydantic import BaseModel
from domain.add_script_mp4s import make_mp4s

router = APIRouter(
    prefix="/mp4",
)


@router.post("/en_script_video/")
async def process_video(file: UploadFile = File(...)):

    save_folder = "pre_mp4"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    file_location = f"{save_folder}/{file.filename}"

    # 파일 시스템에 파일 쓰기
    with open(file_location, "wb") as data:
        shutil.copyfileobj(file.file, data)
    
    language="en"
    real_filename=make_mp4s(file_location,file.filename,language)

    sand_folder="post_mp4"
    send_file_location = f"{sand_folder}/{real_filename}"

    with open(send_file_location, "rb") as data:
        return StreamingResponse(io.BytesIO(data.read()), media_type=file.content_type)



class def_filename(BaseModel):
    filename: str

@router.post("/kr_script_video/")
async def process_video(fileclass: def_filename):
    file_n=fileclass.filename
    
    save_folder = "pre_mp4"

    file_location = f"{save_folder}/{file_n}"
    
    language="kr"
    real_filename=make_mp4s(file_location,file_n,language)

    sand_folder="post_mp4"
    send_file_location = f"{sand_folder}/{real_filename}"
    print("경로확인")
    print(real_filename)
    print(send_file_location)
    
    with open(send_file_location, "rb") as video_file:
        video_stream = io.BytesIO(video_file.read())
        print(type(video_stream))
        return StreamingResponse(video_stream, media_type="video/mp4")

    # def iterfile():  
    #     with open(send_file_location, mode="rb") as file_like:  
    #         yield from file_like  

    # return StreamingResponse(iterfile(), media_type="video/mp4")