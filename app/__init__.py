from io import BytesIO
from typing import Optional

from PIL import Image
from fastapi import FastAPI, HTTPException, UploadFile, File
from loguru import logger

from .infer import InferClient
from .infer.error import LoadError, FileSizeMismatchError, DownloadError
from .settings import InferSettingCurrent
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # List the allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


def verify_token(token):
    # TODO: Implement your token verification logic here
    return True


INFER_APP = InferClient(
    model_name=InferSettingCurrent.wd_model_name,
    model_dir=InferSettingCurrent.wd_model_dir,
    skip_auto_download=InferSettingCurrent.skip_auto_download,
)
logger.info(f"Infer app init success, model_path: {INFER_APP.model_path}")


@app.post("/upload")
async def upload(
    token: Optional[str] = None,
    file: UploadFile = File(...),
    general_threshold: Optional[float] = 0.35,
    character_threshold: Optional[float] = 0.85,
    general_mcut_enabled: Optional[bool] = False,
    character_mcut_enabled: Optional[bool] = False,
):
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        image: Image = Image.open(BytesIO(await file.read()))
        (
            sorted_general_strings,
            rating,
            character_res,
            general_res,
        ) = await INFER_APP.infer(
            image=image,
            general_threshold=general_threshold,
            character_threshold=character_threshold,
            general_mcut_enabled=general_mcut_enabled,
            character_mcut_enabled=character_mcut_enabled,
        )
        logger.warning(
            "tag_result has been deprecated, use sorted_general_strings instead"
        )
        return {
            "tag_result": sorted_general_strings,
            "sorted_general_strings": sorted_general_strings,
            "rating": rating,
            "character_res": character_res,
            "general_res": general_res,
        }
    except LoadError as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))
    except DownloadError as e:
        # 下载模型文件失败
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"Model download failed: {str(e)}")
    except FileSizeMismatchError as e:
        # 下载的模型文件大小不匹配
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="服务器内部错误...")

@app.get("/state")
async def get_state():
    # Check if the infer app has initialized correctly
    if INFER_APP:
        return {"status": "API is running normally", "model_path": INFER_APP.model_path}
    else:
        return {"status": "Infer app initialization failed"}, 500
