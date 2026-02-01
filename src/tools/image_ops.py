"""
image_ops.py - 이미지 분석 도구

GLM-4V (Vision) 모델을 사용하여 이미지를 분석합니다.
"""

import base64
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from src.models import ErrorCode, ToolResponse
from src.core.sandbox import get_sandbox_validator

# ZhipuAI 클라이언트 (glm_cmd와 공유하거나 별도 생성)
try:
    from zhipuai import ZhipuAI
    HAS_ZHIPU = True
except ImportError:
    HAS_ZHIPU = False

class ImageAnalyzeParams(BaseModel):
    """이미지 분석 파라미터"""
    image_path: str = Field(..., description="분석할 이미지 경로")
    prompt: str = Field("Describe this image", description="분석 요청 프롬프트")

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def glm_image_analyze(params: ImageAnalyzeParams) -> ToolResponse:
    if not HAS_ZHIPU:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message="zhipuai 라이브러리가 필요합니다."
        )
        
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        return ToolResponse(
            success=False,
            code=ErrorCode.AUTH_ERROR,
            message="ZHIPU_API_KEY 환경변수가 설정되지 않았습니다."
        )

    try:
        # 샌드박스 검증
        validator = get_sandbox_validator()
        if not validator.validate_path(params.image_path):
             return ToolResponse(
                success=False,
                code=ErrorCode.SANDBOX_VIOLATION,
                message=f"이미지 파일 접근 차단됨 (샌드박스 위반): {params.image_path}"
            )

        # 이미지 존재 확인
        path = Path(params.image_path)
        if not path.exists():
            return ToolResponse(
                success=False,
                code=ErrorCode.FILE_NOT_FOUND,
                message=f"이미지를 찾을 수 없습니다: {params.image_path}"
            )

        # Base64 인코딩
        base64_image = encode_image(params.image_path)
        
        client = ZhipuAI(api_key=api_key)
        
        # GLM-4V 호출
        response = client.chat.completions.create(
            model="glm-4v",  # Vision 모델
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": params.prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_image
                            }
                        }
                    ]
                }
            ]
        )
        
        content = response.choices[0].message.content

        return ToolResponse(
            success=True,
            code=ErrorCode.SUCCESS,
            message="이미지 분석 완료",
            data={
                "analysis": content,
                "model": "glm-4v"
            }
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"이미지 분석 실패: {str(e)}"
        )
