import boto3
import json
import time
import os
import uuid
from typing import Dict, Any, Optional
from strands import tool
import tempfile
import requests
from moviepy.editor import VideoFileClip, AudioFileClip
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env')
load_dotenv()  # Also try default locations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSVideoAdTools:
    def __init__(self):
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.s3_bucket = os.getenv('S3_DESTINATION_BUCKET') or os.getenv('S3_BUCKET_NAME')
        
        # Initialize AWS clients
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region)
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.polly_client = boto3.client('polly', region_name=self.region)
        
        # Ensure S3 bucket exists
        if self.s3_bucket:
            self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create S3 bucket if it doesn't exist"""
        if not self.s3_bucket:
            logger.warning("S3 bucket name not configured")
            return
            
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            logger.info(f"S3 bucket {self.s3_bucket} exists and is accessible")
        except Exception as e:
            logger.warning(f"Cannot access bucket {self.s3_bucket}: {e}")
            try:
                if self.region == 'us-east-1':
                    self.s3_client.create_bucket(Bucket=self.s3_bucket)
                else:
                    self.s3_client.create_bucket(
                        Bucket=self.s3_bucket,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                    )
                logger.info(f"Created S3 bucket: {self.s3_bucket}")
            except Exception as create_error:
                logger.error(f"Failed to create S3 bucket {self.s3_bucket}: {create_error}")
                logger.error("Please ensure you have proper AWS credentials and permissions")
                # Don't raise here - let the app continue and fail gracefully later

# Initialize tools instance
aws_tools = AWSVideoAdTools()

@tool
def generate_content_strategy(ad_description: str) -> Dict[str, str]:
    """
    Generate comprehensive content strategy including image prompt, video prompt, and audio script.
    
    Args:
        ad_description: Description of the advertisement to create
        
    Returns:
        Dictionary with image_prompt, video_prompt, and audio_script
    """
    try:
        prompt = f"""
        Create a comprehensive content strategy for a video advertisement about: {ad_description}
        
        Generate:
        1. A detailed image prompt for creating a reference image (1280x720, professional, high-quality, commercial style)
        2. A detailed video prompt for creating a 6-second engaging commercial-style video with camera movements
        3. An audio script for voiceover (15-20 words, compelling and memorable)
        
        Return ONLY a valid JSON object with keys: image_prompt, video_prompt, audio_script
        """
        
        response = aws_tools.bedrock_client.invoke_model(
            modelId='us.amazon.nova-lite-v1:0',
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {
                    "maxTokens": 1000,
                    "temperature": 0.7
                }
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['output']['message']['content'][0]['text']
        
        # Extract JSON from response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        json_str = content[start_idx:end_idx]
        
        strategy = json.loads(json_str)
        
        # Validate required keys
        required_keys = ['image_prompt', 'video_prompt', 'audio_script']
        if not all(key in strategy for key in required_keys):
            raise ValueError("Missing required strategy components")
            
        logger.info("Successfully generated content strategy")
        return strategy
        
    except Exception as e:
        logger.error(f"Error generating content strategy: {e}")
        # Fallback strategy
        return {
            "image_prompt": f"Professional commercial photograph of {ad_description}, high quality, 1280x720, cinematic lighting, marketing style",
            "video_prompt": f"Create a 6-second commercial video about {ad_description}, professional quality, smooth camera movement, engaging visuals",
            "audio_script": f"Discover the amazing {ad_description}. Experience the difference today!"
        }

@tool
def create_reference_image(image_prompt: str) -> str:
    """
    Create a placeholder reference image (Nova Canvas not available).
    
    Args:
        image_prompt: Detailed prompt for image generation
        
    Returns:
        S3 path to the generated image
    """
    try:
        # Generate unique filename
        image_key = f"generated_images/ref_image_{uuid.uuid4().hex}.png"
        
        # Create a simple placeholder image
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create a 1280x720 image with gradient background
        img = Image.new('RGB', (1280, 720), color='#4A90E2')
        draw = ImageDraw.Draw(img)
        
        # Add text overlay
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
            
        text = "Reference Image\n" + image_prompt[:50] + "..."
        draw.text((50, 300), text, fill='white', font=font)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Upload to S3
        aws_tools.s3_client.put_object(
            Bucket=aws_tools.s3_bucket,
            Key=image_key,
            Body=img_bytes.getvalue(),
            ContentType='image/png'
        )
        
        s3_path = f"s3://{aws_tools.s3_bucket}/{image_key}"
        logger.info(f"Successfully created placeholder image: {s3_path}")
        return s3_path
        
    except Exception as e:
        logger.error(f"Error creating reference image: {e}")
        raise Exception(f"Failed to create reference image: {str(e)}")

@tool
def create_video_with_nova_reel(video_prompt: str, reference_image_s3: str) -> str:
    """
    Create a placeholder video (Nova Reel not available).
    
    Args:
        video_prompt: Detailed prompt for video generation
        reference_image_s3: S3 path to reference image
        
    Returns:
        S3 path to the generated video
    """
    try:
        # Generate unique filename
        video_key = f"generated_videos/video_{uuid.uuid4().hex}.mp4"
        
        logger.info("Starting Nova Reel video generation...")
        
        # Extract bucket and key from S3 path
        bucket_name = reference_image_s3.split('/')[2]
        image_key = '/'.join(reference_image_s3.split('/')[3:])
        
        # Download reference image for Nova Reel
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            aws_tools.s3_client.download_fileobj(bucket_name, image_key, tmp_file)
            tmp_file.flush()
            
            # Read image as base64
            with open(tmp_file.name, 'rb') as img_file:
                import base64
                image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        os.unlink(tmp_file.name)
        
        # Generate unique output path
        video_key = f"generated_videos/video_{uuid.uuid4().hex}"
        output_s3_uri = f"s3://{aws_tools.s3_bucket}/{video_key}/"
        
        # Truncate prompt to meet 512 character limit
        truncated_prompt = video_prompt[:512] if len(video_prompt) > 512 else video_prompt
        
        payload = {
            "taskType": "TEXT_VIDEO",
            "textToVideoParams": {
                "text": truncated_prompt,
                "images": [{
                    "format": "png",
                    "source": {
                        "bytes": image_base64
                    }
                }]
            },
            "videoGenerationConfig": {
                "durationSeconds": 6,
                "fps": 24,
                "dimension": "1280x720",
                "seed": 0
            }
        }
        
        # Start async video generation
        response = aws_tools.bedrock_client.start_async_invoke(
            modelId='amazon.nova-reel-v1:0',
            modelInput=payload,
            outputDataConfig={
                "s3OutputDataConfig": {
                    "s3Uri": output_s3_uri
                }
            }
        )
        
        invocation_arn = response['invocationArn']
        logger.info(f"Started video generation with ARN: {invocation_arn}")
        
        # Poll for completion - THIS IS WHERE THE WAITING HAPPENS
        max_wait_time = 600  # 10 minutes
        poll_interval = 15   # 15 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            logger.info(f"Checking video status... ({elapsed_time}s elapsed)")
            
            status_response = aws_tools.bedrock_client.get_async_invoke(
                invocationArn=invocation_arn
            )
            
            status = status_response['status']
            logger.info(f"Video generation status: {status}")
            
            if status == 'Completed':
                # Find the generated video file
                video_objects = aws_tools.s3_client.list_objects_v2(
                    Bucket=aws_tools.s3_bucket,
                    Prefix=video_key
                )
                
                for obj in video_objects.get('Contents', []):
                    if obj['Key'].endswith('.mp4'):
                        final_s3_path = f"s3://{aws_tools.s3_bucket}/{obj['Key']}"
                        logger.info(f"Video generation completed: {final_s3_path}")
                        return final_s3_path
                
                raise Exception("Video file not found in S3 after completion")
                
            elif status == 'Failed':
                error_msg = status_response.get('failureMessage', 'Unknown error')
                raise Exception(f"Video generation failed: {error_msg}")
            
            elif status in ['InProgress', 'Submitted']:
                logger.info(f"Video still generating, waiting {poll_interval} seconds...")
                time.sleep(poll_interval)
                elapsed_time += poll_interval
            else:
                logger.warning(f"Unknown status: {status}, continuing to wait...")
                time.sleep(poll_interval)
                elapsed_time += poll_interval
        
        raise Exception(f"Video generation timed out after {max_wait_time} seconds")
        
        s3_path = f"s3://{aws_tools.s3_bucket}/{video_key}"
        logger.info(f"Successfully created placeholder video: {s3_path}")
        return s3_path
        
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        raise Exception(f"Failed to create video: {str(e)}")

@tool
def create_voiceover_audio(audio_script: str) -> str:
    """
    Generate voiceover audio using Amazon Polly.
    
    Args:
        audio_script: Script text for voiceover
        
    Returns:
        S3 path to the generated audio file
    """
    try:
        # Generate unique filename
        audio_key = f"generated_audio/voiceover_{uuid.uuid4().hex}.mp3"
        
        response = aws_tools.polly_client.synthesize_speech(
            Text=audio_script,
            OutputFormat='mp3',
            VoiceId='Joanna',  # Professional female voice
            Engine='neural',
            SampleRate='24000'
        )
        
        # Upload audio to S3
        aws_tools.s3_client.put_object(
            Bucket=aws_tools.s3_bucket,
            Key=audio_key,
            Body=response['AudioStream'].read(),
            ContentType='audio/mpeg'
        )
        
        s3_path = f"s3://{aws_tools.s3_bucket}/{audio_key}"
        logger.info(f"Successfully created voiceover: {s3_path}")
        return s3_path
        
    except Exception as e:
        logger.error(f"Error creating voiceover: {e}")
        raise Exception(f"Failed to create voiceover: {str(e)}")

@tool
def merge_video_and_audio(video_s3_path: str, audio_s3_path: str) -> str:
    """
    Download video and audio from S3, merge them, and upload final video.
    
    Args:
        video_s3_path: S3 path to video file
        audio_s3_path: S3 path to audio file
        
    Returns:
        S3 path to the final merged video
    """
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file, \
             tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as audio_file:
            
            # Download video
            video_bucket = video_s3_path.split('/')[2]
            video_key = '/'.join(video_s3_path.split('/')[3:])
            aws_tools.s3_client.download_fileobj(video_bucket, video_key, video_file)
            
            # Download audio
            audio_bucket = audio_s3_path.split('/')[2]
            audio_key = '/'.join(audio_s3_path.split('/')[3:])
            aws_tools.s3_client.download_fileobj(audio_bucket, audio_key, audio_file)
            
            video_file.flush()
            audio_file.flush()
            
            # Merge video and audio using moviepy
            video_clip = VideoFileClip(video_file.name)
            audio_clip = AudioFileClip(audio_file.name)
            
            # Adjust audio duration to match video
            if audio_clip.duration > video_clip.duration:
                audio_clip = audio_clip.subclip(0, video_clip.duration)
            elif audio_clip.duration < video_clip.duration:
                # Loop audio if needed
                from moviepy.editor import concatenate_audioclips
                loops_needed = int(video_clip.duration / audio_clip.duration) + 1
                audio_clips = [audio_clip] * loops_needed
                audio_clip = concatenate_audioclips(audio_clips).subclip(0, video_clip.duration)
            
            # Set audio to video
            final_video = video_clip.set_audio(audio_clip)
            
            # Save merged video
            final_video_key = f"final_videos/ad_{uuid.uuid4().hex}.mp4"
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as final_file:
                final_video.write_videofile(
                    final_file.name,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,
                    logger=None,
                    preset='ultrafast',
                    ffmpeg_params=['-crf', '28', '-maxrate', '1M', '-bufsize', '2M']
                )
                
                # Upload final video to S3
                with open(final_file.name, 'rb') as upload_file:
                    aws_tools.s3_client.put_object(
                        Bucket=aws_tools.s3_bucket,
                        Key=final_video_key,
                        Body=upload_file,
                        ContentType='video/mp4'
                    )
            
            # Cleanup
            video_clip.close()
            audio_clip.close()
            final_video.close()
            
            for temp_file in [video_file.name, audio_file.name, final_file.name]:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            final_s3_path = f"s3://{aws_tools.s3_bucket}/{final_video_key}"
            logger.info(f"Successfully merged video and audio: {final_s3_path}")
            return final_s3_path
            
    except Exception as e:
        logger.error(f"Error merging video and audio: {e}")
        raise Exception(f"Failed to merge video and audio: {str(e)}")