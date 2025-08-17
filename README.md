# AWS Video Ad Creator
Streamlit app that creates video ads using Amazon Bedrock Nova models

## Setup

1. **Install Python 3.10+**

2. **Create virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure AWS credentials in .env:**
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
S3_DESTINATION_BUCKET=your_bucket
```

5. **Run the app:**
```bash
streamlit run auto_video_ad.py
```

## Core Files
- `auto_video_ad.py` - Main Streamlit interface
- `simple_video_ad.py` - AWS Bedrock functions
- `.env` - AWS credentials
- `requirements.txt` - Dependencies

## Features
- Generate prompts with Nova Pro
- Create images with Nova Canvas
- Generate videos with Nova Reel
- Create audio with Amazon Polly
- Merge video and audio with MoviePy