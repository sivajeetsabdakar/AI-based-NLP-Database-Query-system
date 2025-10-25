"""
Security Middleware
Comprehensive security measures for the API
"""
import logging
import time
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import re
import hashlib
import secrets

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware for API protection"""
    
    def __init__(self):
        self.logger = logger
        self.rate_limits = {}  # Simple in-memory rate limiting
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r"<script.*?>.*?</script>",  # XSS patterns
            r"javascript:",  # JavaScript injection
            r"on\w+\s*=",  # Event handlers
            r"union.*select",  # SQL injection
            r"drop\s+table",  # SQL injection
            r"delete\s+from",  # SQL injection
            r"insert\s+into",  # SQL injection
            r"update\s+set",  # SQL injection
            r"exec\s*\(",  # Command injection
            r"system\s*\(",  # Command injection
        ]
    
    async def process_request(self, request: Request) -> Optional[JSONResponse]:
        """Process incoming request for security checks"""
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Check if IP is blocked
            if client_ip in self.blocked_ips:
                self.logger.warning(f"Blocked IP attempted access: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Access denied", "code": "IP_BLOCKED"}
                )
            
            # Rate limiting
            rate_limit_response = self._check_rate_limit(client_ip, request)
            if rate_limit_response:
                return rate_limit_response
            
            # Input validation
            validation_response = self._validate_input(request)
            if validation_response:
                return validation_response
            
            # Security headers
            self._add_security_headers(request)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Security middleware error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Security check failed", "code": "SECURITY_ERROR"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, client_ip: str, request: Request) -> Optional[JSONResponse]:
        """Check rate limiting for client IP"""
        try:
            current_time = time.time()
            window_size = 60  # 1 minute window
            max_requests = 100  # Max requests per window
            
            # Clean old entries
            self.rate_limits = {
                ip: requests for ip, requests in self.rate_limits.items()
                if current_time - requests["last_reset"] < window_size
            }
            
            # Check current IP
            if client_ip not in self.rate_limits:
                self.rate_limits[client_ip] = {
                    "count": 1,
                    "last_reset": current_time
                }
            else:
                ip_data = self.rate_limits[client_ip]
                
                # Reset if window expired
                if current_time - ip_data["last_reset"] >= window_size:
                    ip_data["count"] = 1
                    ip_data["last_reset"] = current_time
                else:
                    ip_data["count"] += 1
                    
                    # Check if limit exceeded
                    if ip_data["count"] > max_requests:
                        self.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                        return JSONResponse(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={
                                "error": "Rate limit exceeded",
                                "code": "RATE_LIMIT_EXCEEDED",
                                "retry_after": window_size
                            }
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Rate limiting error: {str(e)}")
            return None
    
    def _validate_input(self, request: Request) -> Optional[JSONResponse]:
        """Validate input for security threats"""
        try:
            # Check URL for suspicious patterns
            url = str(request.url)
            if self._contains_suspicious_pattern(url):
                self.logger.warning(f"Suspicious URL pattern detected: {url}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid request", "code": "SUSPICIOUS_PATTERN"}
                )
            
            # Check headers for suspicious content
            for header_name, header_value in request.headers.items():
                if self._contains_suspicious_pattern(header_value):
                    self.logger.warning(f"Suspicious header detected: {header_name}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": "Invalid request", "code": "SUSPICIOUS_HEADER"}
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Input validation error: {str(e)}")
            return None
    
    def _contains_suspicious_pattern(self, text: str) -> bool:
        """Check if text contains suspicious patterns"""
        try:
            text_lower = text.lower()
            for pattern in self.suspicious_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return True
            return False
        except Exception:
            return False
    
    def _add_security_headers(self, request: Request):
        """Add security headers to response"""
        # This would be handled by the response middleware
        pass
    
    def block_ip(self, ip: str, reason: str = "Security violation"):
        """Block an IP address"""
        self.blocked_ips.add(ip)
        self.logger.warning(f"IP blocked: {ip}, reason: {reason}")
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip)
        self.logger.info(f"IP unblocked: {ip}")

# Global security middleware instance
security_middleware = SecurityMiddleware()
