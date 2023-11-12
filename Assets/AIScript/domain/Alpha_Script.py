import torch
import openai
import dotenv
import os
import time

from fastapi import APIRouter

from typing import Union
from pydantic import BaseModel

from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    AIMessage,
    HumanMessage,
)
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

import asyncio
import os
from typing import AsyncIterable, Awaitable
from fastapi.responses import StreamingResponse
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.prompts import (
    FewShotChatMessagePromptTemplate,
    ChatPromptTemplate,
)



dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)

key = os.environ["OPENAI_API_KEY"]
openai.api_key = key

router = APIRouter(
    prefix="/chatbot",
)

final_token=""
######################################################
#### 비동기 스트리밍 통신
async def send_message(text: str) -> AsyncIterable[str]:
    final_token=""
    callback = AsyncIteratorCallbackHandler()
    model = ChatOpenAI(
        model_name="gpt-4",
        streaming=True,
        verbose=True,
        callbacks=[callback],
    )
    
    # 시나리오용
    system_messages= '''
    해당 텍스트는 사용자의 경험담이야. 이 이야기로 약 60초 이내의 임팩트 있는 영상을 만들거야.
    1.500자 이내로 쉽게 대학생 말투와 반말로 대본을 만들어줘.
    2.사용자는 상체만 나오고 소품을 활용하지 않아.
    3.행동은 3개 이내로 괄호()안에 지시어로 작성해줘.
    3.한 문장이 끝날때 마다 "|"이 기호로 표현해줘
    4. 좋아요와 구독 관련된 이야기는 말하지마
    5. 사용자의 입력이 영어인지 한국어인지 판단후 다음의 순서를 따라가줘
    6. 사용자의 입력이 한국어일때
    6-1.한국어로 말한 경우 영상 제목, 오프닝, 내용, 결론 순으로 한국어로 답변해줘
    6-2. 만약 사용자의 입력이 한국어 이고 시나리오로 변환하기 어렵다면 "시나리오를 생성하기 위해 더 다양한 이야기를 해주세요"라는 답변을 보내줘
    7. 사용자의 입력이 영어일때
    7-1.영어로 말한경우 Video title, opening, content, conclusion 순으로 영어로 답변해줘
    7-2.만약 사용자의 입력이 영어 이고 시나리오로 변환하기 어렵다면 "Please tell me more diverse stories to create scenarios"라는 답변을 보내줘
    '''

    # ## 테스트용
    # system_messages="10글자 이내로 답해줘"


    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        try:
            await fn
        except Exception as e:
            print(f"Caught exception: {e}")
        finally:
            # Signal the aiter to stop.
            event.set()

    # Begin a task that runs in the background.
    
    few_shot_input1 = '''
        내가 외국에서 자주듣는말이 있어
        1. BTS알아?
        2. 북한이야 남한이야?
        3. 나 김치알아
        이렇게 있는데 이 세가지로 쇼츠 대본을 만들어줘
    '''
    few_shot_output1='''
    제목: "외국에서 BTS와 김치 얘기, 대체 왜?"|

    오프닝:|
    (작은 웃음으로 카메라를 바라봄)|
    "안녕? 난 대학생이야." |
    (손가락 세 개를 펼치면서)|
    "오늘 나랑 함께 외국에서 맨날 듣는 세 가지 말에 대해 이야기해 볼까?" | 

    내용:|
    (한 손으로 1의 동작을 하며)|
    "첫번째, 'BTS 알아?' 요즘 외국에서 젤 많이 듣는 말이지." |
    "한국인 보면 만나는 사람마다 다 BTS을 물어봐." |
    "이게 왜인지 알아?" |
    "한류의 위력이야. 인터넷 세상에서 BTS는 상상을 벗어난 인기를 얻고 있어." |

    (한 손으로 2의 동작을 하며)|
    "두번째, '북한이야 남한이야?' 내가 한국인인걸 알아차렸다면, 이게 바로 다음 질문이지." |
    "대체 왜 북한과 남한을 따지는 건지... 사실 나도 몰라." |
    "아마 북한과 남한이 다르다는 것을 알고 있긴 하지만 그게 어떤 건지 확실히 모르는 거 같아." | 

    (한 손으로 3의 동작을 하며)|
    "마지막, '나 김치 알아.' 아, 이게 진짜 웃겨." |
    "처음엔 좀 놀랐지만 이제 이 말에 익숙해졌어." |
    "다들 한국 음식에 대해 어느 정도 알고 있다는 것을 인정받고 싶은 거 같아." |

    결론 :|
    "그래서 이 세 가지 말을 외국에서 자주 듣는 것에 대해 어떻게 생각해?" |
    "그냥 웃기고 흥미로운 경험이야. 내가 한국인이라는 사실에 더 자부심을 가지게 해." |
    "이런 일화들을 통해 나도 스스로를 재검토하고 세상을 더 폭넓게 볼 수 있는 기회가 되더라고." |
    (일어나며, 카메라로 손을 흔듬) |
    "그럼 다음에 또 이런 이야기로 찾아올게. 바이바이~!"
    '''


    few_shot_input2='''
    하하하
    '''
    few_shot_output2='''
    시나리오를 생성하기 위해 더 다양한 이야기를 해주세요
    '''

    # Begin a task that runs in the background.
    task = asyncio.create_task(wrap_done(
        model.agenerate(messages=[[SystemMessage(content=system_messages),HumanMessage(content=few_shot_input1),
                                   AIMessage(content=few_shot_output1),HumanMessage(content=few_shot_input2),
                                   AIMessage(content=few_shot_output2),  HumanMessage(content=text)]]),
        callback.done),
    )



    n=0
    async for token in callback.aiter():
        print(n,end=" ")
        n+=1
        print(token)
        final_token+=token
        yield f"data: {token}\n\n"
    print("출력결과 : ")
    print(final_token)
    await task

class StreamRequest(BaseModel):
    """Request body for streaming."""
    text: str


@router.post("/test_text")
def stream(body: StreamRequest):
    

    print(body.text)

    return StreamingResponse(send_message(body.text), media_type="text/event-stream")
######################################################



######################################################
### 이미지 분류 통신
class Image_connect(BaseModel):
    text: str


@router.post("/image_connect")
def image_def(input: Image_connect):
    print(input.text)

    system = '''
        장소 = {"home","library","Campus","classroom","park","office"}
        1. 사용자의 시나리오를 보고 알려준 장소 중 1가지로 분류해줘
        2. 보기에 해당되지 않는 경우, 실외라면 "park", 실내라면 "home"으로 분류해줘.
        3. 장소에 해당되지 않는 입력이면 "home"으로 분류해줘
        4. 입력이 없으면 "home"만 나타내줘
        5. 출력으로는 장소만 나타내줘 
        
        '''
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": ""},
        {"role": "assistant", "content": "home"},
        {"role": "user", "content": input.text}
    ]

    chat_completion = openai.ChatCompletion.create(  ## gpt 오브젝트 생성후 메세지 전달
        model="gpt-4",
        # model="gpt-4",
        messages=messages,
        temperature=1,
        max_tokens=1000
    )
    
    result = chat_completion.choices[0].message.content
    print("분류결과 : "+result)
    return {"place" : result}
######################################################


######################################################
### 음악 분류 통신
class Sound_connect(BaseModel):
    text: str


@router.post("/music_connect")
def Sound_def(input: Sound_connect):
    print(input.text)

    system = '''
        장소 = {"Chill","Cool","Dramatic","Happy","Mysterious","Peaceful","Sad","Serious"}
        1. 사용자의 시나리오를 보고 알려준 시나리오의 무드 중 1가지로 분류해줘
        2. 무드를 분류할 수 없는 입력이면 "Peaceful"으로 분류해줘
        3. 입력이 없으면 "Peaceful"만 나타내줘
        5. 출력으로는 Mood만 나타내줘 
        '''
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": ""},
        {"role": "assistant", "content": "Peaceful"},
        {"role": "user", "content": input.text}
    ]

    chat_completion = openai.ChatCompletion.create(  ## gpt 오브젝트 생성후 메세지 전달
        model="gpt-4",
        # model="gpt-4",
        messages=messages,
        temperature=1,
        max_tokens=1000
    )
    
    result = chat_completion.choices[0].message.content
    print("분류결과 : "+result)
    return {"mood" : result}
######################################################