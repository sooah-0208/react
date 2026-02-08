from fastapi import FastAPI, File, UploadFile
from pathlib import Path
from fastapi.responses import HTMLResponse, FileResponse
import shutil

app = FastAPI()

# --- [설정 영역] ---
# 업로드된 파일이 저장될 폴더 경로 설정 (현재 폴더 아래 'uploads' 폴더) -> 자동적으로 서버 키기 전에 uploads 폴더 생성됨(전역 변수)
UPLOAD_DIR = Path("uploads")
# 해당 폴더가 없으면 생성 (exist_ok=True는 이미 폴더가 있어도 에러를 내지 말라는 뜻)
UPLOAD_DIR.mkdir(exist_ok=True)

# (참고) 확장자 제한과 최대 용량 설정 - 실제 로직에 적용 전 단계
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB (바이트 단위 계산)

# --- [기능 1: 메인 화면] ---
@app.get("/", response_class=HTMLResponse)
def main():
    """
    사용자가 파일을 선택할 수 있는 아주 간단한 HTML 폼을 브라우저에 띄워줍니다.
    """
    html = """
    <body>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" />
            <button type="submit">등록</button>
        </form>
    </body>
    """
    return html 

  # 웹 브라우저가 서버로 데이터를 보낼 때는 보통 이름표(name): 실제데이터 쌍으로 묶어서 보냅니다.
        # HTML: <input type="file" name="file" />
        # # 서버(FastAPI): async def upload_file(file: UploadFile = File(...)):
        # 여기서 HTML의 name="file"과 FastAPI 함수의 매개변수 이름인 file이 서로 일치해야 합니다. 
        # 만약 HTML에서 name="my_image"라고 바꾼다면, FastAPI 코드도 my_image: UploadFile로 바꿔야 서버가 "아, 이게 그 데이터구나!" 하고 알아먹습니다.
        # 왜 하필 이름이 'file'인가요?
        # 사실 file 대신 user_photo, upload_data 등 아무 이름이나 써도 상관없습니다. 다만:
        # 관례상: 파일 업로드니까 직관적으로 file이라고 짓는 경우가 많습니다.
        # 매칭: 서버 코드에서 file: UploadFile이라고 변수명을 정해두었기 때문에, HTML에서도 그에 맞춰 name="file"을 써준 것입니다.



# --- [기능 2: 파일 업로드] ---
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)): 
    """
    사용자가 보낸 파일을 서버 하드디스크에 저장하는 핵심 로직입니다.
    """
    # 1. 저장할 전체 경로 생성 (uploads/파일명.jpg)
    file_path = UPLOAD_DIR / file.filename
    
    # 2. 서버에 새 파일을 생성하고 내용을 복사함
    # "wb" -> Write Binary (이진 쓰기 모드)
    # with: 파일을 다 쓴 뒤 자동으로 닫아주는 안전장치입니다. (발표 시: "자원 누수를 막기 위해 사용했습니다"라고 하면 가산점!)
    # open("wb"): "자, 이제 이미지 데이터를 있는 그대로 쏟아부을 빈 파일을 준비해!"라는 뜻입니다.
    #  발표 시 예상 질문 (Q&A)
    # Q: 만약 wb 대신 w를 쓰면 어떻게 되나요? 
    # A: "이미지 데이터는 텍스트가 아니기 때문에 UnicodeEncodeError 같은 에러가 발생하거나, 강제로 저장하더라도 이미지가 깨져서 보이지 않게 됩니다."
    with file_path.open("wb") as buffer:
        # shutil.copyfileobj: 파일 객체를 효율적으로 복사 (메모리 낭비 방지)


        shutil.copyfileobj(file.file, buffer)

    # 3. 처리가 끝나면 사용자에게 결과 전송
    return {
        "message": "업로드 완료",
        "filename": file.filename,
    }

# --- [기능 3: 파일 다운로드/조회] ---
@app.get("/download")
async def download_image(filename: str):  ## 비동기 방식(async)을 사용이유: 원래는 직렬로서 하나 실행되면 하나끝나고 실행되어야하는데 병렬로 지정하여 동시에 실행할 수 있도록 지정해준 것임.
    """
    저장된 파일의 이름을 받아서 클라이언트에게 파일을 전송합니다.
    사용법: http://127.0.0.1:8000/download?filename=이미지명.jpg
    """
    # 저장 경로에서 해당 파일 이름이 있는지 확인
    file_path = UPLOAD_DIR / filename
    
    # FileResponse: FastAPI가 제공하는 파일 전송 전용 응답 클래스
    return FileResponse(path=file_path, filename=filename)  ## 파일이 있어야 다운로드가 됨 , "마지막으로 FileResponse에서 filename을 한 번 더 써준 이유는, 사용자가 이 파일을 받을 때 서버에 저장된 이름 그대로 안전하게 다운로드받을 수 있도록 브라우저에게 가이드를 주기 위함입니다."