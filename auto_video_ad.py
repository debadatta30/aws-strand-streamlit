import streamlit as st
import json
import time
from simple_video_ad import create_prompts, create_image_and_save_s3, create_video_with_image
import boto3
from datetime import datetime
import moviepy.editor as mp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Auto Video Ad Creator", layout="wide")
st.title("🎬 Auto Video Ad Creator")
st.write("Watch the AI agent create your video ad automatically!")

# Input
ad_description = st.text_input("Describe your video ad:", placeholder="A luxury car driving through mountain roads at sunset")

if st.button("Create Video Ad", type="primary") and ad_description:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Create Prompts
    status_text.text("🤖 Step 1/5: Creating prompts...")
    progress_bar.progress(20)
    
    with st.spinner("AI is generating optimized prompts..."):
        prompts = create_prompts(ad_description)
        time.sleep(1)
    
    st.success("✅ Prompts created!")
    with st.expander("View Generated Prompts"):
        st.text(prompts)
    
    try:
        prompt_data = json.loads(prompts)
        image_prompt = prompt_data['image_prompt']
        video_prompt = prompt_data['video_prompt']
        audio_script = prompt_data['audio_script']
    except:
        image_prompt = f"Professional image for: {ad_description}"
        video_prompt = f"Professional video ad for: {ad_description}"
        audio_script = f"Experience {ad_description}. Available now."
    
    # Step 2: Create Image
    status_text.text("🎨 Step 2/5: Generating image with Nova Canvas...")
    progress_bar.progress(40)
    
    with st.spinner("Creating reference image..."):
        image_path = create_image_and_save_s3(image_prompt)
        time.sleep(1)
    
    st.success(f"✅ Image created: {image_path}")
    
    # Step 3: Create Video
    status_text.text("🎬 Step 3/5: Creating video with Nova Reel...")
    progress_bar.progress(60)
    
    with st.spinner("Generating video (this may take a few minutes)..."):
        video_result = create_video_with_image(video_prompt, image_path)
        if "ARN:" in video_result:
            video_arn = video_result.split("ARN: ")[1].split(".")[0]
        time.sleep(2)
    
    st.success("✅ Video generation started!")
    
    # Wait for video completion
    status_text.text("⏳ Waiting for video generation to complete...")
    bedrock = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
    
    while True:
        try:
            response = bedrock.get_async_invoke(invocationArn=video_arn)
            status = response["status"]
            
            if status == "Completed":
                st.success("✅ Video completed!")
                break
            elif status == "Failed":
                st.error("❌ Video generation failed")
                st.stop()
            else:
                st.info(f"🔄 Video status: {status}")
                time.sleep(10)
        except Exception as e:
            st.error(f"Error checking video status: {str(e)}")
            break
    
    # Step 4: Create Audio
    status_text.text("🎧 Step 4/5: Generating audio with Amazon Polly...")
    progress_bar.progress(80)
    
    with st.spinner("Creating voiceover..."):
        polly_client = boto3.client('polly', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
        s3_client = boto3.client('s3', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
        
        response = polly_client.synthesize_speech(
            Text=audio_script,
            OutputFormat='mp3',
            VoiceId='Joanna',
            Engine='neural'
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_s3_key = f"audio/ad_audio_{timestamp}.mp3"
        
        s3_client.put_object(
            Bucket=os.getenv('S3_DESTINATION_BUCKET', 'deb-banners'),
            Key=audio_s3_key,
            Body=response['AudioStream'].read(),
            ContentType='audio/mpeg'
        )
        
        audio_path = f"s3://{os.getenv('S3_DESTINATION_BUCKET', 'deb-banners')}/{audio_s3_key}"
    
    st.success(f"✅ Audio created: {audio_path}")
    
    # Step 5: Merge Video and Audio
    status_text.text("🎭 Step 5/5: Merging video and audio...")
    progress_bar.progress(100)
    
    with st.spinner("Creating final video with audio..."):
        s3_prefix = video_arn.split('/')[-1]
        bucket = os.getenv('S3_DESTINATION_BUCKET', 'deb-banners')
        
        # Use unique filenames
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        video_file = f'temp_video_{unique_id}.mp4'
        audio_file = f'temp_audio_{unique_id}.mp3'
        output_file = f'final_video_{unique_id}.mp4'
        
        try:
            s3_client.download_file(bucket, f"output/{s3_prefix}/output.mp4", video_file)
            s3_client.download_file(bucket, audio_s3_key, audio_file)
            
            # Merge with moviepy
            video_clip = mp.VideoFileClip(video_file)
            audio_clip = mp.AudioFileClip(audio_file)
            
            min_duration = min(video_clip.duration, audio_clip.duration)
            video_trimmed = video_clip.subclipped(0, min_duration)
            audio_trimmed = audio_clip.subclipped(0, min_duration)
            
            final_clip = video_trimmed.with_audio(audio_trimmed)
            final_clip.write_videofile(output_file)
            
            # Close clips before cleanup
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            # Upload final video
            final_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            final_s3_key = f"final/ad_final_{final_timestamp}.mp4"
            
            with open(output_file, 'rb') as f:
                s3_client.put_object(
                    Bucket=bucket,
                    Key=final_s3_key,
                    Body=f.read(),
                    ContentType='video/mp4'
                )
        
        finally:
            # Cleanup with error handling
            import os as file_os
            for temp_file in [video_file, audio_file, output_file]:
                try:
                    if file_os.path.exists(temp_file):
                        file_os.remove(temp_file)
                except:
                    pass
        
        final_video_path = f"s3://{bucket}/{final_s3_key}"
    
    status_text.text("🎉 Video ad creation completed!")
    st.success(f"🎬 Final video with audio: {final_video_path}")
    
    # Try to display video
    try:
        display_file = f"display_{unique_id}.mp4"
        s3_client.download_file(bucket, final_s3_key, display_file)
        st.video(display_file)
    except Exception as e:
        st.info(f"Video ready in S3: {final_video_path}")

st.write("---")
st.write("*Powered by Amazon Bedrock Nova models*")