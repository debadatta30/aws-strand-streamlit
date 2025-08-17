import boto3
import json
import base64
import random
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

S3_DESTINATION_BUCKET = os.getenv('S3_DESTINATION_BUCKET', 'deb-banners')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

def create_prompts(ad_description):
    """Create image and video prompts from ad description."""
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)
        
        prompt = f"""Create detailed prompts for a video advertisement based on this description: {ad_description}

Generate:
1. IMAGE_PROMPT: A detailed prompt for creating a reference image (1280x720, professional, high-quality)
2. VIDEO_PROMPT: A detailed prompt for creating a video ad (6 seconds, engaging, commercial-style)

Format as JSON:
{{"image_prompt": "...", "video_prompt": "..."}}"""

        request_body = {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        response = bedrock.invoke_model(
            modelId="us.amazon.nova-pro-v1:0",
            body=json.dumps(request_body)
        )
        
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text']
        
    except Exception as e:
        return f"Error creating prompts: {str(e)}"

def create_image_and_save_s3(image_prompt):
    """Create image from prompt and save to S3."""
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        request_body = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": image_prompt
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "height": 720,
                "width": 1280,
                "cfgScale": 8.0,
                "seed": random.randint(0, 2147483648)
            }
        }
        
        response = bedrock.invoke_model(
            modelId="amazon.nova-canvas-v1:0",
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        image_data = base64.b64decode(response_body['images'][0])
        
        # Save to S3
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"images/ad_image_{timestamp}.png"
        
        s3_client.put_object(
            Bucket=S3_DESTINATION_BUCKET,
            Key=s3_key,
            Body=image_data,
            ContentType='image/png'
        )
        
        return f"s3://{S3_DESTINATION_BUCKET}/{s3_key}"
        
    except Exception as e:
        return f"Error creating image: {str(e)}"

def create_video_with_image(video_prompt, image_s3_path):
    """Create video using Nova Reel with reference image."""
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        # Download image from S3
        bucket = image_s3_path.split('/')[2]
        key = '/'.join(image_s3_path.split('/')[3:])
        
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_data = response['Body'].read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Create video (truncate prompt to 512 chars max)
        truncated_prompt = video_prompt[:512] if len(video_prompt) > 512 else video_prompt
        
        model_input = {
            "taskType": "TEXT_VIDEO",
            "textToVideoParams": {
                "text": truncated_prompt,
                "images": [{"format": "png", "source": {"bytes": image_base64}}]
            },
            "videoGenerationConfig": {
                "durationSeconds": 6,
                "fps": 24,
                "dimension": "1280x720",
                "seed": random.randint(0, 2147483648)
            }
        }
        
        invocation = bedrock.start_async_invoke(
            modelId="amazon.nova-reel-v1:0",
            modelInput=model_input,
            outputDataConfig={"s3OutputDataConfig": {"s3Uri": f"s3://{S3_DESTINATION_BUCKET}/output/"}}
        )
        
        invocation_arn = invocation["invocationArn"]
        s3_prefix = invocation_arn.split('/')[-1]
        
        return f"Video generation started. ARN: {invocation_arn}. Video will be at: s3://{S3_DESTINATION_BUCKET}/output/{s3_prefix}/output.mp4"
        
    except Exception as e:
        return f"Error creating video: {str(e)}"

def create_video_ad(ad_description):
    """Complete video ad creation pipeline."""
    print("Step 1: Creating prompts...")
    prompts = create_prompts(ad_description)
    print(f"Prompts: {prompts}")
    
    # Extract prompts (simplified - assumes JSON format)
    try:
        prompt_data = json.loads(prompts)
        image_prompt = prompt_data['image_prompt']
        video_prompt = prompt_data['video_prompt']
    except:
        image_prompt = f"Professional image for: {ad_description}"
        video_prompt = f"Professional video ad for: {ad_description}"
    
    print("Step 2: Creating and saving image...")
    image_path = create_image_and_save_s3(image_prompt)
    print(f"Image saved: {image_path}")
    
    print("Step 3: Creating video...")
    video_result = create_video_with_image(video_prompt, image_path)
    print(f"Video result: {video_result}")
    
    return video_result

if __name__ == "__main__":
    ad_description = input("Describe your video ad: ")
    result = create_video_ad(ad_description)