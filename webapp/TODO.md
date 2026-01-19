# WebApp TODO - Remaining Implementation

## Critical Items

### 1. API Endpoint for initData Validation

**File to create**: `d:\Proj\bananapicsbot\api\app\api\v1\endpoints\webapp.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import hashlib
import hmac
from urllib.parse import parse_qsl

router = APIRouter()

class InitDataRequest(BaseModel):
    init_data: str

@router.post("/validate")
async def validate_init_data(request: InitDataRequest):
    """Validate Telegram WebApp initData"""
    # Parse initData
    data_dict = dict(parse_qsl(request.init_data))

    # Extract hash
    received_hash = data_dict.pop('hash', None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash")

    # Get BOT_TOKEN from environment
    import os
    bot_token = os.getenv('BOT_TOKEN')

    # Create data check string
    data_check_string = '\\n'.join(f"{k}={v}" for k, v in sorted(data_dict.items()))

    # Calculate secret key
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    # Calculate hash
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    # Verify hash
    if calculated_hash != received_hash:
        raise HTTPException(status_code=401, detail="Invalid initData")

    # Extract user data
    import json
    user_data = json.loads(data_dict.get('user', '{}'))

    return {
        "user": {
            "id": user_data.get("id"),
            "first_name": user_data.get("first_name"),
            "username": user_data.get("username"),
        }
    }
```

**Then register in**: `d:\Proj\bananapicsbot\api\app\api\v1\api.py`

```python
from .endpoints import webapp

api_router.include_router(webapp.router, prefix="/webapp", tags=["webapp"])
```

### 2. Environment Variables

Add to all `.env.*` files:

```env
WEBAPP_URL=http://localhost:8080  # or your production domain
```

### 3. Docker Compose

**File**: `docker-compose.yml`

Add webapp service after celery-beat (around line 69):

```yaml
webapp:
  build:
    context: ./webapp
  image: ghcr.io/blogchik/bananapicsbot/webapp:latest
  ports:
    - "8080:80"
  networks:
    - app_net
  restart: unless-stopped
```

### 4. Bot Configuration

Update the webapp command handler if needed to use the environment variable:

```python
import os
webapp_url = os.getenv("WEBAPP_URL", "https://your-domain.com")
```

## Testing Checklist

- [ ] Build and start all Docker services
- [ ] Test `/webapp` command in Telegram bot
- [ ] Verify WebApp button appears
- [ ] Click button and verify webapp opens in Telegram
- [ ] Test authentication with initData
- [ ] Test text-to-image generation
- [ ] Test image-to-image generation with file upload
- [ ] Test watermark remover
- [ ] Test profile page display
- [ ] Test referral link copy
- [ ] Verify all animations work
- [ ] Test on different screen sizes
- [ ] Check balance updates after generation

## Production Deployment

1. Set `WEBAPP_URL` to your actual domain
2. Ensure WebApp is accessible publicly
3. Configure SSL/TLS for secure connection
4. Test initData validation thoroughly
5. Monitor logs for any errors

## Optional Enhancements

- Add generation history in profile
- Add more tools (upscale, style transfer, etc.)
- Add favorites/bookmarks for generated images
- Add sharing functionality
- Add more detailed error messages
- Add loading skeletons instead of spinners
- Add image zoom/preview modal
- Add batch generation support
