import streamlit as st
import json
import time
import boto3
import os
import tempfile
import logging
from enhanced_agent_config import create_video_advertisement
from enhanced_tools import aws_tools
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env')
load_dotenv()  # Also try default locations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="AWS Video Ad Creator", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        # Test AWS connection
        boto3.client('bedrock-runtime', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
        return True
    except Exception as e:
        st.error(f"AWS credentials not configured properly: {e}")
        return False

def download_and_display_video(s3_path: str):
    """Download video from S3 and display in Streamlit"""
    try:
        # Extract bucket and key
        bucket = s3_path.split('/')[2]
        key = '/'.join(s3_path.split('/')[3:])
        
        # Download to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            aws_tools.s3_client.download_fileobj(bucket, key, tmp_file)
            tmp_file.flush()
            
            # Display video in Streamlit
            with open(tmp_file.name, 'rb') as video_file:
                video_bytes = video_file.read()
                st.video(video_bytes)
            
            # Cleanup
            os.unlink(tmp_file.name)
            
    except Exception as e:
        st.error(f"Error displaying video: {e}")
        st.info(f"Video available at: {s3_path}")

def main():
    st.title("🎬 AWS Video Ad Creator")
    st.markdown("### Create professional video advertisements using AWS AI services")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # AWS Region
        region = st.selectbox(
            "AWS Region",
            ["us-east-1", "us-west-2", "eu-west-1"],
            index=0
        )
        
        # S3 Bucket
        bucket_name = st.text_input(
            "S3 Bucket Name",
            value=os.getenv('S3_DESTINATION_BUCKET', ''),
            help="Bucket for storing generated media"
        )
        
        # Update environment
        os.environ['AWS_DEFAULT_REGION'] = region
        os.environ['S3_DESTINATION_BUCKET'] = bucket_name
        
        st.markdown("---")
        st.markdown("**Requirements:**")
        st.markdown("- AWS credentials configured")
        st.markdown("- Amazon Bedrock model access")
        st.markdown("- S3 bucket for media storage")
    
    # Check prerequisites
    if not check_aws_credentials():
        st.stop()
    
    if not bucket_name:
        st.warning("Please configure S3 bucket name in the sidebar")
        st.stop()
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Advertisement Description")
        ad_description = st.text_area(
            "Describe your video advertisement:",
            placeholder="A luxury electric car driving through scenic mountain roads at golden hour, showcasing sustainability and performance",
            height=100
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            col3, col4 = st.columns(2)
            
            with col3:
                video_duration = st.slider("Video Duration (seconds)", 3, 10, 6)
                video_quality = st.selectbox("Video Quality", ["720p", "1080p"], index=0)
            
            with col4:
                voice_selection = st.selectbox(
                    "Voice Selection", 
                    ["Joanna", "Matthew", "Salli", "Joey"], 
                    index=0
                )
                audio_style = st.selectbox("Audio Style", ["Professional", "Casual", "Energetic"], index=0)
    
    with col2:
        st.subheader("Creation Status")
        status_container = st.container()
    
    # Create video button
    if st.button("🚀 Create Video Advertisement", type="primary", disabled=not ad_description):
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Results container
        results_container = st.container()
        
        with status_container:
            st.info("Starting video advertisement creation...")
        
        try:
            # Step 1: Content Strategy
            status_text.text("🧠 Step 1/5: Generating content strategy...")
            progress_bar.progress(20)
            
            with st.spinner("Creating content strategy..."):
                from enhanced_tools import generate_content_strategy
                strategy = generate_content_strategy(ad_description)
            
            st.success("✅ Content strategy created!")
            
            with st.expander("View Generated Strategy"):
                st.json(strategy)
            
            # Step 2: Reference Image
            status_text.text("🖼️ Step 2/5: Creating reference image...")
            progress_bar.progress(40)
            
            with st.spinner("Generating reference image with Nova Canvas..."):
                from enhanced_tools import create_reference_image
                image_s3_path = create_reference_image(strategy['image_prompt'])
            
            st.success("✅ Reference image created!")
            st.info(f"📁 Image: {image_s3_path}")
            
            # Step 3: Video Generation
            status_text.text("🎥 Step 3/5: Creating video with Nova Reel...")
            progress_bar.progress(60)
            
            with st.spinner("Generating video... This may take a few minutes."):
                from enhanced_tools import create_video_with_nova_reel
                video_s3_path = create_video_with_nova_reel(
                    strategy['video_prompt'], 
                    image_s3_path
                )
            
            st.success("✅ Video created!")
            st.info(f"📁 Video: {video_s3_path}")
            
            # Step 4: Audio Generation
            status_text.text("🎵 Step 4/5: Creating voiceover...")
            progress_bar.progress(80)
            
            with st.spinner("Generating voiceover with Amazon Polly..."):
                from enhanced_tools import create_voiceover_audio
                audio_s3_path = create_voiceover_audio(strategy['audio_script'])
            
            st.success("✅ Voiceover created!")
            st.info(f"📁 Audio: {audio_s3_path}")
            
            # Step 5: Final Merge
            status_text.text("🔧 Step 5/5: Merging video and audio...")
            progress_bar.progress(100)
            
            with st.spinner("Merging video and audio..."):
                from enhanced_tools import merge_video_and_audio
                final_video_s3_path = merge_video_and_audio(video_s3_path, audio_s3_path)
            
            st.success("🎉 Video advertisement completed!")
            status_text.text("✅ All steps completed successfully!")
            
            # Display final result
            st.subheader("🎬 Final Video Advertisement")
            st.info(f"📁 Final Video: {final_video_s3_path}")
            
            # Try to display video
            st.subheader("Preview")
            download_and_display_video(final_video_s3_path)
            
            # Summary
            with st.expander("Creation Summary"):
                summary = {
                    "Description": ad_description,
                    "Strategy": strategy,
                    "Reference Image": image_s3_path,
                    "Generated Video": video_s3_path,
                    "Voiceover Audio": audio_s3_path,
                    "Final Video": final_video_s3_path
                }
                st.json(summary)
                
        except Exception as e:
            st.error(f"❌ Error during creation: {str(e)}")
            logger.error(f"Video creation error: {e}")
            
            # Display partial results if available
            if 'strategy' in locals():
                st.subheader("Partial Results")
                st.json({"strategy": strategy})

    # Footer
    st.markdown("---")
    st.markdown("*Powered by AWS Strand Agents, Amazon Bedrock Nova models, and Amazon Polly*")

if __name__ == "__main__":
    main()