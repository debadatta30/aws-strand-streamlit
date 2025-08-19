# AWS Video Ad Creator with Strands Agents

An AI-powered video advertisement creation tool using AWS services and Strands Agents framework.

## Features

- **AI-Driven Content Strategy**: Generates comprehensive content strategies using Amazon Nova Lite
- **Image Generation**: Creates reference images with Amazon Nova Canvas
- **Video Creation**: Produces videos using Amazon Nova Reel with reference images
- **Voice Synthesis**: Generates professional voiceovers with Amazon Polly
- **Video Processing**: Merges video and audio using MoviePy
- **Agent Orchestration**: Uses Strands Agents to coordinate the entire workflow

## Architecture

The application uses a **VideoAdAgent** that orchestrates five main steps:

1. **Content Strategy Generation** - Creates detailed prompts for image, video, and audio
2. **Reference Image Creation** - Generates a base image using Nova Canvas
3. **Video Generation** - Creates video content using Nova Reel with the reference image
4. **Audio Generation** - Synthesizes voiceover using Amazon Polly
5. **Final Assembly** - Merges video and audio into the final advertisement

## Prerequisites

### AWS Services Access
- Amazon Bedrock with Nova models (Nova Lite, Nova Canvas, Nova Reel)
- Amazon Polly
- Amazon S3

### Environment Setup
1. **AWS Credentials**: Configure AWS credentials via AWS CLI or environment variables
2. **S3 Bucket**: Create an S3 bucket for storing generated media
3. **FFmpeg**: Required for video processing (install via `pip install imageio-ffmpeg`)

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd claude
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_DESTINATION_BUCKET=your-bucket-name
```

## Usage

### Running the Streamlit App

```bash
streamlit run streamlit_agent.py
```

### Using the Application

1. **Enter Description**: Describe your video advertisement in the text area
2. **Create Video**: Click "Create Video Ad" to start the process
3. **Monitor Progress**: Watch the progress bar and status updates
4. **View Results**: 
   - Expand "View Strategy" to see generated prompts
   - Expand "View File Paths" to see S3 locations
   - Watch the final video in the preview player

## Key Components

### VideoAdAgent Class
- **Purpose**: Orchestrates the entire video creation workflow
- **Model**: Uses `us.amazon.nova-lite-v1:0` for agent reasoning
- **Tools**: Integrates all five creation tools

### Tools Integration
- **generate_content_strategy**: Creates detailed prompts for each media type
- **create_reference_image**: Generates base images with Nova Canvas
- **create_video_with_nova_reel**: Creates videos with proper async waiting
- **create_voiceover_audio**: Synthesizes speech with Amazon Polly
- **merge_video_and_audio**: Combines media using MoviePy

### Error Handling
- **Fallback Mechanisms**: Direct tool calls if agent parsing fails
- **Robust Parsing**: Handles malformed JSON responses
- **Progress Tracking**: Real-time status updates during generation

## File Structure

```
claude/
├── streamlit_agent.py          # Main Streamlit application
├── enhanced_tools.py           # AWS service integration tools
├── enhanced_agent_config.py    # Agent configuration
├── enhanced_streamlit_app.py   # Alternative direct implementation
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # This file
```

## Troubleshooting

### Common Issues

1. **Model Access Denied**
   - Request access to Nova models in AWS Bedrock console
   - Ensure proper IAM permissions

2. **S3 Bucket Issues**
   - Verify bucket exists and is accessible
   - Check S3 permissions for read/write operations

3. **Video Generation Timeout**
   - Nova Reel can take 5-10 minutes for video generation
   - The app waits up to 10 minutes with status polling

4. **FFmpeg Errors**
   - Install: `pip install imageio-ffmpeg`
   - Ensure sufficient system memory for video processing

### Performance Notes

- **Video Generation**: 5-10 minutes (Nova Reel processing time)
- **Image Generation**: 10-30 seconds (Nova Canvas)
- **Audio Generation**: 5-10 seconds (Amazon Polly)
- **Final Assembly**: 30-60 seconds (MoviePy processing)

## Dependencies

```
strands-agents>=0.1.0
streamlit>=1.24.0
boto3>=1.26.0
python-dotenv>=1.0.0
moviepy>=1.0.3
Pillow>=9.5.0
opencv-python>=4.8.0
imageio-ffmpeg>=0.2.0
requests>=2.31.0
```

## License

This project is for demonstration purposes. Ensure compliance with AWS service terms and usage policies.