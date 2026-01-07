"""Thread worker for processing transcripts with AI providers."""
from PyQt5.QtCore import QThread, pyqtSignal
import re
import logging

from src.providers import AIProviderFactory


class AIProcessingThread(QThread):
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    processing_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    chunk_size = 3000

    def __init__(self, input_file, output_file, api_key, selected_model_name, output_language, chunk_size, prompt,
                 provider_name):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.selected_model_name = selected_model_name
        self.output_language = output_language
        self.prompt = prompt
        self.provider_name = provider_name
        self._is_running = True
        logging.basicConfig(filename='ai_processing.log', level=logging.ERROR,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def run(self):
        try:
            # Create provider instance using factory
            self.provider = AIProviderFactory.create_provider(
                self.provider_name,
                self.api_key,
                self.selected_model_name
            )
            self.provider.configure()

            video_chunks = self.split_videos(self.input_file)
            final_output_path = self.output_file
            response_file_path = self.output_file.replace(".txt", "_temp_response.txt")
            total_videos = len(video_chunks) - 1 if len(video_chunks) > 1 else 0

            with open(response_file_path, "w", encoding="utf-8") as response_file:
                response_file.write("")

            for video_index, video_chunk in enumerate(video_chunks[1:]):
                if not self._is_running:
                    return
                self.status_update.emit(
                    f"\nProcessing Video {video_index + 1}/{total_videos}: Preview: {video_chunk[:50]}...")
                word_count = len(video_chunk.split())
                self.status_update.emit(f"Word Count: {word_count} words")
                self.status_update.emit(f"Chunk Size: {self.chunk_size} words")

                video_transcript_chunks = self.split_text_into_chunks(video_chunk, self.chunk_size)
                previous_response = ""
                for chunk_index, chunk in enumerate(video_transcript_chunks):
                    if not self._is_running:
                        return
                    if previous_response:
                        context_prompt = (
                            "The following text is a continuation... "
                            f"Previous response:\n{previous_response}\n\nNew text to process(Do Not Repeat the Previous response:):\n"
                        )
                    else:
                        context_prompt = ""

                    formatted_prompt = self.prompt.replace("[Language]", self.output_language)
                    full_prompt = f"{context_prompt}{formatted_prompt}\n\n{chunk}"

                    self.status_update.emit(
                        f"Generating {self.provider_name} response for Video {video_index + 1}/{total_videos}, Chunk {chunk_index + 1}/{len(video_transcript_chunks)}, please wait...")

                    try:
                        response_text = self.provider.generate_content(full_prompt)

                    except ValueError as e:
                        # Content blocked or safety error
                        error_msg = self.provider.handle_error(e)
                        self.status_update.emit(
                            f"<font color='#f472b6'>Warning: {error_msg}. Skipping chunk.</font>")
                        # Skip this chunk and continue with the next one
                        continue
                    except Exception as e:
                        # Handle other potential API errors
                        error_msg = self.provider.handle_error(e)
                        self.error_occurred.emit(error_msg)
                        return  # Stop processing on other errors

                    with open(response_file_path, "a", encoding="utf-8") as response_file:
                        response_file.write(response_text + "\n\n")
                    previous_response = response_text
                    self.status_update.emit(
                        f"Chunk {chunk_index + 1}/{len(video_transcript_chunks)} processed and saved to temp file.")

                self.status_update.emit(
                    f"All {self.provider_name} responses for video {video_index + 1} have been saved to temp file.")

                with open(response_file_path, "r", encoding="utf-8") as response_file:
                    video_response_content = response_file.read()

                with open(final_output_path, "a", encoding="utf-8") as final_output_file:
                    final_output_file.write(
                        f"Video URL: {video_chunks[video_index + 1].splitlines()[0].replace('Video URL: ', '')}\n")
                    final_output_file.write(video_response_content + "\n\n")

                with open(response_file_path, "w", encoding="utf-8") as response_file:
                    response_file.write("")

                progress_percent = int(((video_index + 1) / total_videos) * 100) if total_videos > 0 else 100
                self.progress_update.emit(progress_percent)
                self.status_update.emit(
                    f"Final {self.provider_name} output for video {video_index + 1} appended to {final_output_path}")

            self.status_update.emit(
                f"All {self.provider_name} responses for all videos have been saved to {final_output_path}.")
            self.processing_complete.emit(final_output_path)
            self.progress_update.emit(100)
        except Exception as e:
            error_message = f"{self.provider_name} error: {str(e)}"
            self.error_occurred.emit(error_message)
            logging.error(error_message)

    def split_text_into_chunks(self, text, chunk_size, min_chunk_size=500):
        words = text.split()
        chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        if len(chunks) > 1 and len(chunks[-1].split()) < min_chunk_size:
            chunks[-2] += " " + chunks[-1]
            chunks.pop()
        return chunks

    def split_videos(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        video_chunks = re.split(r'(?=Video URL:)', content)
        video_chunks = [chunk.strip() for chunk in video_chunks if chunk.strip()]
        return video_chunks

    def stop(self):
        self._is_running = False
