from strands import Agent
from enhanced_tools import (
    generate_content_strategy,
    create_reference_image,
    create_video_with_nova_reel,
    create_voiceover_audio,
    merge_video_and_audio
)
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_video_ad_agent():
    """Create a Strands agent for video ad creation"""
    
    agent = Agent(
        name="VideoAdCreator",
        description="""
        I am an AI agent specialized in creating video advertisements using AWS services.
        I can generate comprehensive video ads by:
        1. Creating content strategy with prompts
        2. Generating reference images with Nova Canvas
        3. Creating videos with Nova Reel
        4. Generating voiceover with Polly
        5. Merging video and audio into final product
        """,
        tools=[
            generate_content_strategy,
            create_reference_image,
            create_video_with_nova_reel,
            create_voiceover_audio,
            merge_video_and_audio
        ]
    )
    
    return agent

def create_video_advertisement(ad_description: str):
    """
    Complete workflow to create a video advertisement
    
    Args:
        ad_description: Description of the advertisement to create
        
    Returns:
        Dictionary with results from each step
    """
    agent = create_video_ad_agent()
    results = {}
    
    try:
        # Step 1: Generate content strategy
        logger.info("Step 1: Generating content strategy...")
        strategy_prompt = f"""
        Create a content strategy for a video advertisement about: {ad_description}
        Use the generate_content_strategy tool to create detailed prompts.
        """
        
        strategy_result = agent(strategy_prompt)
        results['strategy'] = strategy_result
        
        # Extract strategy data (this would need parsing from agent response)
        # For simplicity, calling tool directly here
        strategy_data = generate_content_strategy(ad_description)
        results['strategy_data'] = strategy_data
        
        # Step 2: Create reference image
        logger.info("Step 2: Creating reference image...")
        image_prompt = f"""
        Create a reference image using the image prompt: {strategy_data['image_prompt']}
        Use the create_reference_image tool.
        """
        
        image_result = agent(image_prompt)
        results['image'] = image_result
        
        # Get actual S3 path
        image_s3_path = create_reference_image(strategy_data['image_prompt'])
        results['image_s3_path'] = image_s3_path
        
        # Step 3: Create video
        logger.info("Step 3: Creating video with Nova Reel...")
        video_prompt = f"""
        Create a video using the video prompt: {strategy_data['video_prompt']}
        Use the reference image at: {image_s3_path}
        Use the create_video_with_nova_reel tool.
        """
        
        video_result = agent(video_prompt)
        results['video'] = video_result
        
        # Get actual S3 path
        video_s3_path = create_video_with_nova_reel(
            strategy_data['video_prompt'], 
            image_s3_path
        )
        results['video_s3_path'] = video_s3_path
        
        # Step 4: Create voiceover
        logger.info("Step 4: Creating voiceover audio...")
        audio_prompt = f"""
        Create voiceover audio using the script: {strategy_data['audio_script']}
        Use the create_voiceover_audio tool.
        """
        
        audio_result = agent(audio_prompt)
        results['audio'] = audio_result
        
        # Get actual S3 path
        audio_s3_path = create_voiceover_audio(strategy_data['audio_script'])
        results['audio_s3_path'] = audio_s3_path
        
        # Step 5: Merge video and audio
        logger.info("Step 5: Merging video and audio...")
        merge_prompt = f"""
        Merge the video at {video_s3_path} with the audio at {audio_s3_path}
        Use the merge_video_and_audio tool.
        """
        
        merge_result = agent(merge_prompt)
        results['merge'] = merge_result
        
        # Get final S3 path
        final_s3_path = merge_video_and_audio(video_s3_path, audio_s3_path)
        results['final_video_s3_path'] = final_s3_path
        
        logger.info("Video advertisement creation completed successfully!")
        return results
        
    except Exception as e:
        logger.error(f"Error in video advertisement creation: {e}")
        results['error'] = str(e)
        return results