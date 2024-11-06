import os
import pickle
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import openai  # Import OpenAI for AI integration
from dotenv import load_dotenv  # For loading environment variables securely

# Load environment variables from a .env file
load_dotenv()

# Authenticate with Google API for YouTube
def authenticate_youtube():
    """
    Authenticates the user to access the YouTube API. The authentication credentials are stored 
    in 'token.json' for future use to avoid re-authentication.

    Returns:
        youtube: A YouTube API client instance.
    """
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]  # Permission scope for uploading videos
    
    creds = None

    # Check if token.json exists to retrieve stored credentials
    if os.path.exists('token.json'):
        try:
            with open('token.json', 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Error loading credentials: {e}")

    # If credentials are not valid, re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh expired credentials
        else:
            try:
                # Initiate OAuth flow to get new credentials
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.getenv('GOOGLE_CLIENT_SECRETS_FILE'), SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Error during authentication: {e}")
                return None
        
        # Save the credentials for future use
        try:
            with open('token.json', 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"Error saving credentials: {e}")

    # Build and return the YouTube API client
    try:
        youtube = build("youtube", "v3", credentials=creds)
        return youtube
    except Exception as e:
        print(f"Error building YouTube API client: {e}")
        return None

# Function to generate video metadata using AI (OpenAI)
def generate_metadata(video_file):
    """
    Generates video title, description, and tags using OpenAI's GPT-3 model based on the video file name.
    
    Args:
        video_file (str): The name of the video file for which metadata is to be generated.
    
    Returns:
        tuple: A tuple containing the generated title, description, and tags.
    """
    openai.api_key = os.getenv('OPENAI_API_KEY')  # Load OpenAI API key from environment variables

    # Provide context or prompt for generating title and description based on video file
    prompt = f"Generate a YouTube video title, description, and tags for a video about {video_file}"

    try:
        # Call OpenAI API to generate metadata
        response = openai.Completion.create(
            model="gpt-3.5-turbo",  # Updated model
            prompt=prompt,
            max_tokens=200
        )
        
        # Extract the title, description, and tags from the AI response
        ai_generated_text = response.choices[0].text.strip().split('\n')
        title = ai_generated_text[0]
        description = ai_generated_text[1] if len(ai_generated_text) > 1 else "No description provided."
        tags = ai_generated_text[2:] if len(ai_generated_text) > 2 else ["AI", "auto-upload", "python"]

        return title, description, tags
    except Exception as e:
        print(f"Error generating metadata: {e}")
        return None, None, []

# Function to upload the video to YouTube
def upload_video(youtube, video_path, title, description, tags, category_id, privacy_status):
    """
    Uploads the video to YouTube with the specified metadata (title, description, tags, etc.).
    
    Args:
        youtube: A YouTube API client instance.
        video_path (str): Path to the video file.
        title (str): The title of the video.
        description (str): The description of the video.
        tags (list): The tags associated with the video.
        category_id (str): The category ID for the video.
        privacy_status (str): The privacy status for the video ('public', 'private', 'unlisted').
    
    Returns:
        None
    """
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }

    # Upload the video using the YouTube API
    media_file = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media_file
        )

        print(f"Starting upload for video: {title}...")
        response = request.execute()

        if 'id' in response:
            print(f"Upload successful! Video ID: {response['id']}")
            print(f"Video URL: https://www.youtube.com/watch?v={response['id']}")
        else:
            print("Upload failed. Please check the details.")
    except Exception as e:
        print(f"Error uploading video: {e}")

# Main function to execute the video upload task
def main():
    """
    Main function that authenticates with YouTube, generates metadata using AI, and uploads the video.
    """
    video_path = "1105.mp4"  # Path to your video file
    category_id = "22"  # Example: "22" for People & Blogs category
    privacy_status = "public"  # Options: "public", "private", "unlisted"

    youtube = authenticate_youtube()  # Authenticate YouTube

    if youtube:
        # Generate metadata using AI
        title, description, tags = generate_metadata(video_path)

        # Upload the video with AI-generated metadata
        if title and description:
            upload_video(youtube, video_path, title, description, tags, category_id, privacy_status)
        else:
            print("Metadata generation failed, video upload aborted.")

if __name__ == "__main__":
    main()
