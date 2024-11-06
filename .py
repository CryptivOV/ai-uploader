import os
import pickle
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import openai  # Import OpenAI for AI integration

# Authenticate with Google API for YouTube
def authenticate_youtube():
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    creds = None

    if os.path.exists('token.json'):
        with open('token.json', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'your-client-secrets-file.json', SCOPES)  # Replace with your client secrets file
            creds = flow.run_local_server(port=0)
        with open('token.json', 'wb') as token:
            pickle.dump(creds, token)
    
    youtube = build("youtube", "v3", credentials=creds)
    return youtube

# Function to generate video metadata using AI (OpenAI)
def generate_metadata(video_file):
    openai.api_key = "your-openai-api-key"  # Replace with your OpenAI API key

    # Provide context or prompt for generating title and description based on video file
    prompt = f"Generate a YouTube video title, description, and tags for a video about {video_file}"

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

# Function to upload the video to YouTube
def upload_video(youtube, video_path, title, description, category_id, privacy_status):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,  # Use the generated tags here
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }

    media_file = MediaFileUpload(video_path, chunksize=-1, resumable=True)
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

# Function to run the upload task
def main():
    video_path = "your-video-file-path.mp4"  # Replace with your video file path
    category_id = "22"  # Example: "22" for People & Blogs category
    privacy_status = "public"  # Options: "public", "private", "unlisted"

    youtube = authenticate_youtube()  # Authenticate YouTube

    # Generate metadata using AI
    title, description, tags = generate_metadata(video_path)

    # Upload the video with AI-generated metadata
    upload_video(youtube, video_path, title, description, category_id, privacy_status)

if __name__ == "__main__":
    main()
