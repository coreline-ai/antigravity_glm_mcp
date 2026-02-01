"""
http_ops.py - HTTP 요청 도구

외부 REST API를 호출합니다.
"""

import asyncio
import json
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from src.models import ErrorCode, ToolResponse

class HttpRequestParams(BaseModel):
    """HTTP 요청 파라미터"""
    url: str = Field(..., description="요청 URL")
    method: str = Field("GET", description="HTTP 메소드 (GET, POST, PUT, DELETE)")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP 헤더")
    body: Optional[Any] = Field(None, description="요청 본문 (JSON 데이터 등)")
    timeout: int = Field(30, description="타임아웃 (초)")

async def glm_http_request(params: HttpRequestParams) -> ToolResponse:
    if not HAS_REQUESTS:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message="requests 라이브러리가 필요합니다."
        )

    # 보안: SSRF 방어 고도화 (도메인 해석, IP 대역 검증, DNS Rebinding 방지)
    import socket
    import ipaddress
    from urllib.parse import urlparse

    try:
        parsed_url = urlparse(params.url)
        host = parsed_url.hostname
        if not host:
            return ToolResponse(
                success=False,
                code=ErrorCode.INVALID_PARAMS,
                message=f"유효하지 않은 URL 형식입니다: {params.url}"
            )

        # 1. 도메인/주소를 모든 가능한 IP로 해석 (SSRF 방지의 핵심)
        # getaddrinfo는 정수 IP(2130706433), Hex IP, Octal IP, 도메인을 모두 실제 IP로 변환함
        port = parsed_url.port or (80 if parsed_url.scheme == 'http' else 443)
        addr_info = socket.getaddrinfo(host, port)
        
        # 해석된 IP들 중 하나라도 내부망 주소면 차단
        resolved_ips = []
        for family, kind, proto, canonname, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)
            resolved_ips.append(ip_str)
            
            # 사설, 루프백, 링크 로컬 등 내부망 대역 차단
            if (ip_obj.is_private or 
                ip_obj.is_loopback or 
                ip_obj.is_link_local or 
                ip_obj.is_multicast or
                ip_obj.is_reserved):
                return ToolResponse(
                    success=False,
                    code=ErrorCode.SANDBOX_VIOLATION,
                    message=f"보안상 허용되지 않는 네트워크 주소입니다: {host} (해석된 IP: {ip_str})"
                )
        
        # 2. DNS Rebinding 방어: 검증된 IP로만 요청을 보내도록 설정
        # requests가 다시 DNS 해석을 하지 않도록 URL의 호스트를 IP로 교체
        verified_ip = resolved_ips[0]
        netloc = verified_ip
        if parsed_url.port:
            netloc = f"{verified_ip}:{parsed_url.port}"
        
        target_url = parsed_url._replace(netloc=netloc).geturl()
        
    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INVALID_PARAMS,
            message=f"URL 주소 해석 실패: {str(e)}"
        )

    try:
        # 동기 requests를 비동기로 실행
        loop = asyncio.get_running_loop()
        
        method = params.method.upper()
        
        # 원래의 호스트명을 Host 헤더로 보존하여 가상 호스트 대응
        headers = params.headers or {}
        headers['Host'] = host
        
        kwargs = {
            "url": target_url,  # IP로 치환된 URL 사용 (DNS Rebinding 방어)
            "headers": headers,
            "timeout": params.timeout,
            "verify": False if parsed_url.scheme == 'https' else True # IP 요청 시 인증서 검토 우회 (필요시)
        }
        
        if params.body:
            if isinstance(params.body, dict) or isinstance(params.body, list):
                kwargs["json"] = params.body
            else:
                kwargs["data"] = str(params.body)

        response = await loop.run_in_executor(
            None,
            lambda: requests.request(method, **kwargs)
        )

        # 응답 처리
        response_data = None
        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text

        return ToolResponse(
            success=200 <= response.status_code < 300,
            code=ErrorCode.SUCCESS if 200 <= response.status_code < 300 else ErrorCode.INTERNAL_ERROR,
            message=f"HTTP {method} 완료 ({response.status_code})",
            data={
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": response_data
            }
        )

    except Exception as e:
        return ToolResponse(
            success=False,
            code=ErrorCode.INTERNAL_ERROR,
            message=f"HTTP 요청 실패: {str(e)}"
        )
