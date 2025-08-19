# streamlit_with_agents.py
import streamlit as st
from strands import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')
load_dotenv()

from enhanced_tools import (
    generate_content_strategy,
    create_reference_image,
    create_video_with_nova_reel,
    create_voiceover_audio,
    merge_video_and_audio
)

class VideoAdAgent:
    def __init__(self):
        # Create the main agent with all tools
        self.agent = Agent(
            name="VideoAdCreator",
            description="AI agent for creating video advertisements",
            model="us.amazon.nova-lite-v1:0",
            tools=[
                generate_content_strategy,
                create_reference_image,
                create_video_with_nova_reel,
                create_voiceover_audio,
                merge_video_and_audio
            ]
        )
    
    def create_video_ad(self, ad_description: str) -> dict:
        """Use agent to create complete video ad"""
        
        # Step 1: Agent creates strategy
        strategy_prompt = f"""
        Create a content strategy for: {ad_description}
        
        Use the generate_content_strategy tool with the description: {ad_description}
        
        The tool will return a JSON with image_prompt, video_prompt, and audio_script.
        """
        
        strategy_response = self.agent(strategy_prompt)
        
        # Parse strategy from agent response
        strategy_data = self._parse_strategy_from_response(strategy_response, ad_description)
        
        # Step 2: Agent creates image
        import streamlit as st
        if 'status_text' in st.session_state:
            st.session_state.status_text.text("🖼️ Step 2/5: Creating reference image...")
            st.session_state.progress_bar.progress(40)
        
        image_prompt = f"""
        Create a reference image using this prompt: {strategy_data['image_prompt']}
        Use the create_reference_image tool and return the S3 path.
        """
        
        image_response = self.agent(image_prompt)
        image_s3_path = self._parse_s3_path_from_response(image_response)
        
        # Fallback: call tool directly if parsing failed
        if not image_s3_path:
            image_s3_path = create_reference_image(strategy_data['image_prompt'])
        
        # Step 3: Agent creates video
        video_prompt = f"""
        Create a video using this prompt: {strategy_data['video_prompt']}
        Use the reference image at: {image_s3_path}
        Use the create_video_with_nova_reel tool and return the S3 path.
        """
        
        video_response = self.agent(video_prompt)
        video_s3_path = self._parse_s3_path_from_response(video_response)
        
        # Fallback: call tool directly if parsing failed
        if not video_s3_path:
            video_s3_path = create_video_with_nova_reel(strategy_data['video_prompt'], image_s3_path)
        
        # Step 4: Agent creates audio
        audio_prompt = f"""
        Create voiceover audio with this script: {strategy_data['audio_script']}
        Use the create_voiceover_audio tool and return the S3 path.
        """
        
        audio_response = self.agent(audio_prompt)
        audio_s3_path = self._parse_s3_path_from_response(audio_response)
        
        # Fallback: call tool directly if parsing failed
        if not audio_s3_path:
            audio_s3_path = create_voiceover_audio(strategy_data['audio_script'])
        
        # Step 5: Agent merges video and audio
        merge_prompt = f"""
        Merge the video at {video_s3_path} with audio at {audio_s3_path}
        Use the merge_video_and_audio tool and return the final S3 path.
        """
        
        final_response = self.agent(merge_prompt)
        final_s3_path = self._parse_s3_path_from_response(final_response)
        
        # Fallback: call tool directly if parsing failed
        if not final_s3_path:
            final_s3_path = merge_video_and_audio(video_s3_path, audio_s3_path)
        
        return {
            'strategy': strategy_data,
            'image_path': image_s3_path,
            'video_path': video_s3_path,
            'audio_path': audio_s3_path,
            'final_path': final_s3_path
        }
    
    def _parse_strategy_from_response(self, response, ad_description=""):
        """Extract strategy JSON from agent response"""
        try:
            import json
            response_text = str(response)
            
            # Try to find JSON in the response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                
                # Fix common JSON formatting issues
                import re
                # Add missing commas between fields
                json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)
                json_str = re.sub(r'"\s*"', '","', json_str)
                
                strategy = json.loads(json_str)
                
                # Validate required keys
                required_keys = ['image_prompt', 'video_prompt', 'audio_script']
                if all(key in strategy for key in required_keys):
                    return strategy
            
            # Fallback strategy using actual ad description
            return {
                "image_prompt": f"Professional commercial photograph of {ad_description}, high quality, 1280x720, cinematic lighting, marketing style",
                "video_prompt": f"Create a 6-second commercial video about {ad_description}, professional quality, smooth camera movement, engaging visuals",
                "audio_script": f"Discover the amazing {ad_description}. Experience the difference today!"
            }
        except Exception as e:
            # Fallback if parsing fails
            return {
                "image_prompt": f"Professional commercial photograph of {ad_description}, high quality, 1280x720, cinematic lighting, marketing style",
                "video_prompt": f"Create a 6-second commercial video about {ad_description}, professional quality, smooth camera movement, engaging visuals", 
                "audio_script": f"Discover the amazing {ad_description}. Experience the difference today!"
            }
    
    def _parse_s3_path_from_response(self, response):
        """Extract S3 path from agent response"""
        try:
            response_text = str(response)
            # Look for s3:// pattern
            import re
            s3_match = re.search(r's3://[^\s"\)\]`]+', response_text)
            if s3_match:
                return s3_match.group(0).strip('`"\' ')
            
            # If no S3 path found, return None to trigger direct tool call
            return None
        except:
            return None

# Streamlit App
def main():
    st.title("🎬 AWS Video Ad Creator with Agents")
    
    # Initialize agent
    if 'video_agent' not in st.session_state:
        st.session_state.video_agent = VideoAdAgent()
    
    ad_description = st.text_area("Describe your video ad:")
    
    if st.button("Create Video Ad") and ad_description:
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🧠 Step 1/5: Generating content strategy...")
            progress_bar.progress(20)
            
            results = st.session_state.video_agent.create_video_ad(ad_description)
            
            progress_bar.progress(100)
            status_text.text("✅ All steps completed successfully!")
            
            st.success("Video ad created successfully!")
            
            # Show results in expandable sections
            with st.expander("View Strategy"):
                st.json(results['strategy'])
            
            with st.expander("View File Paths"):
                st.write(f"**Image:** {results['image_path']}")
                st.write(f"**Video:** {results['video_path']}")
                st.write(f"**Audio:** {results['audio_path']}")
                st.write(f"**Final:** {results['final_path']}")
                
            # Display final video if available
            if results.get('final_path'):
                try:
                    # Download and display video from S3
                    s3_path = results['final_path'].strip('`"\' ')
                    bucket = s3_path.split('/')[2]
                    key = '/'.join(s3_path.split('/')[3:])
                    
                    import tempfile
                    import boto3
                    import os
                    
                    s3_client = boto3.client('s3')
                    
                    # Create temporary file without context manager to avoid file lock
                    tmp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                    try:
                        s3_client.download_fileobj(bucket, key, tmp_file)
                        tmp_file.flush()
                        tmp_file.close()  # Close the file handle
                        
                        # Display video in Streamlit
                        with open(tmp_file.name, 'rb') as video_file:
                            video_bytes = video_file.read()
                            st.video(video_bytes)
                    finally:
                        # Cleanup
                        try:
                            os.unlink(tmp_file.name)
                        except:
                            pass
                except Exception as e:
                    st.error(f"Error displaying video: {e}")
                    st.info(f"Video available at: {results['final_path']}")
                
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()