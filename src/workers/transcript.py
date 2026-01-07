"""Thread worker for extracting YouTube transcripts."""
from PyQt5.QtCore import QThread, pyqtSignal
from pytube import Playlist
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound


class TranscriptExtractionThread(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    extraction_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, playlist_url, output_file):
        super().__init__()
        self.playlist_url = playlist_url
        self.output_file = output_file
        self._is_running = True

    def run(self):
        try:
            url = self.playlist_url

            if "playlist?list=" in url:
                playlist = Playlist(url)
                video_urls = playlist.video_urls
                total_videos = len(video_urls)
                playlist_name = playlist.title
            elif "watch?v=" in url:
                video_urls = [url]
                total_videos = 1
                playlist_name = "Single Video"
            else:
                # Handle invalid URL case
                self.error_occurred.emit("Invalid URL provided. Please use a valid YouTube video or playlist URL.")
                return

            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(f"Playlist Name: {playlist_name}\n\n")
                for index, video_url in enumerate(video_urls, 1):
                    if not self._is_running:
                        return

                    try:
                        video_id = video_url.split("?v=")[1].split("&")[0]
                        fetched_transcript = None  # Initialize for this video

                        ytt_api = YouTubeTranscriptApi()

                        # 1. Get the list of all available transcripts
                        transcript_list_obj = ytt_api.list(video_id)

                        # 2. Try to find and fetch English first
                        try:
                            transcript_object = transcript_list_obj.find_transcript(['en'])
                            self.status_update.emit(
                                f"Found English transcript for video {index}/{total_videos}. Fetching...")
                            fetched_transcript = transcript_object.fetch()

                        # 3. If English is not found, fallback to the first available transcript
                        except NoTranscriptFound:
                            self.status_update.emit(
                                f"English not found for video {index}/{total_videos}. Trying fallback...")
                            # Get the first transcript object from the list
                            first_transcript_object = next(iter(transcript_list_obj))
                            self.status_update.emit(
                                f"Found fallback: '{first_transcript_object.language}'. Fetching...")
                            fetched_transcript = first_transcript_object.fetch()

                        # 4. If we successfully got a transcript, process and write it
                        if fetched_transcript:

                            transcript = ' '.join([segment.text for segment in fetched_transcript])

                            f.write(f"Video URL: {video_url}\n")
                            f.write(transcript + '\n\n')
                            self.status_update.emit(f"Extracted transcript for video {index}/{total_videos}")
                        else:

                            self.status_update.emit(
                                f"Could not find any usable transcript for video {index}/{total_videos} ({video_url})")

                        progress_percent = int((index / total_videos) * 100)
                        self.progress_update.emit(progress_percent)

                    # 5. This 'except' catches if a video has NO transcripts at all
                    except NoTranscriptFound:
                        self.status_update.emit(
                            f"Error: No transcripts found for video {index}/{total_videos} ({video_url})")
                    except Exception as video_error:
                        self.status_update.emit(f"Error processing {video_url}: {str(video_error)}")

            self.extraction_complete.emit(self.output_file)
        except Exception as e:
            self.error_occurred.emit(f"Extraction error: {str(e)}")

    def stop(self):
        self._is_running = False
