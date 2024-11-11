# linkedin_api.py
import os
from typing import Optional, Dict, List, Union, Any
import requests
from requests.adapters import HTTPAdapter, Retry
import json
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class LinkedInScope(Enum):
    """Current LinkedIn OAuth 2.0 Scopes"""
    OPENID = "openid"
    PROFILE = "profile"
    EMAIL = "email"
    SHARE = "w_member_social"

class Visibility(Enum):
    """Post visibility options"""
    PUBLIC = "PUBLIC"
    CONNECTIONS = "CONNECTIONS"

@dataclass
class PostResponse:
    """Response data for post operations"""
    status: str
    post_id: str
    details: Optional[Dict] = None

class LinkedInError(Exception):
    """Base exception for LinkedIn API errors"""
    pass

class LinkedInPost:
    """LinkedIn Post Manager with current OAuth scope support"""
    
    BASE_URL = "https://api.linkedin.com/v2"
    API_VERSION = "202304"
    
    def __init__(
        self,
        access_token: str,
        log_dir: str = "logs",
        debug: bool = False
    ):
        """
        Initialize LinkedIn Post Manager
        
        Args:
            access_token (str): LinkedIn OAuth 2.0 access token
            log_dir (str): Directory for storing logs
            debug (bool): Enable debug logging
        """
        self.access_token = access_token
        self.log_dir = Path(log_dir)
        self.debug = debug
        self._setup_logging()
        self._setup_session()
        self._validate_token()

    def _setup_logging(self) -> None:
        """Configure logging with both file and console handlers"""
        self.log_dir.mkdir(exist_ok=True)
        
        log_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / 'linkedin.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('LinkedInPost')

    def _setup_session(self) -> None:
        """Set up requests session with retry logic"""
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _get_headers(self) -> Dict[str, str]:
        """Create headers required for LinkedIn API requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
            'LinkedIn-Version': self.API_VERSION
        }

    def _validate_token(self) -> None:
        """Validate the access token using userinfo endpoint"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/userinfo",
                headers=self._get_headers()
            )
            response.raise_for_status()
            self.user_info = response.json()
            self.user_urn = f"urn:li:person:{self.user_info['sub']}"
            self.logger.info("Successfully validated access token")
            
            if self.debug:
                self.logger.debug(f"User Info: {json.dumps(self.user_info, indent=2)}")
                
        except requests.exceptions.RequestException as e:
            error_msg = (
                f"Token validation failed: {str(e)}\n"
                "Please ensure:\n"
                "1. Your access token is valid and not expired\n"
                "2. You have the required scopes (openid, profile, w_member_social)\n"
                "3. Your application is properly configured in LinkedIn Developer Portal"
            )
            self.logger.error(error_msg)
            raise LinkedInError(error_msg)

    def create_text_post(
        self,
        text: str,
        visibility: Union[Visibility, str] = Visibility.PUBLIC
    ) -> PostResponse:
        """
        Create a text-only post on LinkedIn
        
        Args:
            text (str): Post content
            visibility (Union[Visibility, str]): Post visibility setting
            
        Returns:
            PostResponse: Response containing post details
        """
        if not text.strip():
            raise ValueError("Post text cannot be empty")

        # Handle string visibility input
        if isinstance(visibility, str):
            try:
                visibility = Visibility(visibility.upper())
            except ValueError:
                raise ValueError(
                    f"Invalid visibility value. Must be one of: "
                    f"{', '.join(v.value for v in Visibility)}"
                )

        post_data = {
            "author": self.user_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility.value
            }
        }

        try:
            self.logger.info("Creating text post...")
            if self.debug:
                self.logger.debug(f"Post data: {json.dumps(post_data, indent=2)}")
            
            response = self.session.post(
                f"{self.BASE_URL}/ugcPosts",
                headers=self._get_headers(),
                json=post_data
            )
            response.raise_for_status()
            
            post_id = response.headers.get('x-restli-id')
            if not post_id:
                raise LinkedInError("No post ID received in response")
            
            self.logger.info(f"Successfully created post with ID: {post_id}")
            
            return PostResponse(
                status="success",
                post_id=post_id,
                details={"timestamp": datetime.now().isoformat()}
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to create post: {str(e)}"
            self.logger.error(error_msg)
            raise LinkedInError(error_msg)

def create_post(
    access_token: str,
    message: str,
    visibility: str = "PUBLIC",
    debug: bool = False
) -> Dict[str, Any]:
    """
    Convenient function to create a LinkedIn post
    
    Args:
        access_token (str): LinkedIn OAuth 2.0 access token
        message (str): Post content
        visibility (str): Post visibility (PUBLIC or CONNECTIONS)
        debug (bool): Enable debug logging
    """
    try:
        linkedin = LinkedInPost(
            access_token=access_token,
            debug=debug
        )
        
        response = linkedin.create_text_post(
            text=message,
            visibility=visibility
        )
        
        return {
            "success": True,
            "post_id": response.post_id,
            "status": response.status,
            "details": response.details
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": e.__class__.__name__
        }

# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    ACCESS_TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not ACCESS_TOKEN:
        print("Error: LINKEDIN_ACCESS_TOKEN environment variable not set")
        exit(1)
    
    # Example post
    message = """🚀 Excited to share my latest project!

I've been working on improving Python implementations for better code quality.

#Python #Programming #Innovation"""
    
    result = create_post(
        access_token=ACCESS_TOKEN,
        message=message,
        debug=True  # Enable debug logging
    )
    
    if result["success"]:
        print(f"Post created successfully!")
        print(f"Post ID: {result['post_id']}")
    else:
        print(f"Failed to create post:")
        print(f"Error type: {result['error_type']}")
        print(f"Error message: {result['error']}")