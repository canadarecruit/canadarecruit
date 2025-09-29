# cloudinary_config.py
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

def config_cloudinary():
    cloudinary.config(
        cloud_name="dglguwew3",
        api_key="797289117876647",
        api_secret="pI3GX9CchdXdAwYzV2YUcX_AN4I",  
        secure=True
    )