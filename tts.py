import json
import websockets
import asyncio
import queue
import io
import numpy as np
import sounddevice as sd
from pydub import AudioSegment
import base64
import time

class ElevenLabsManager:
    def __init__(self, api_key, model_id, voice_id, websocket_uri, subtitle_window, sample_rate = 44100, channels = 2, min_audio_before_playback = 1, max_character_in_subtitles = 60, subtitle_font = "font.otf", output_colors = ("rgb(100, 255, 100)", "white")):
        self.model_id = model_id
        self.voice_id = voice_id
        self.websocket_uri = websocket_uri
        self.websocket_object = websockets.connect(websocket_uri, max_size=16 * 1024 * 1024, additional_headers={"xi-api-key": api_key})
        self.audio_queue = queue.Queue()
        self.audio_buffer_list = []
        self.sample_rate = sample_rate
        self.channels = channels
        self.min_audio_before_playback = min_audio_before_playback
        self.internal_buffer = np.zeros((0, channels), dtype=np.float32)
        self.alignment = []
        self.audio_queued = 0
        # This will be a list of pairs (in list format), each pair containing a word and its start time in ms
        self.word_alignment = []
        self.time = 0
        self.current_words = []
        self.max_character_in_subtitles = max_character_in_subtitles
        # self.subtitle_app_thread = threading.Thread(target=self.run_subtitle_window, daemon=True, args = (subtitle_font, 24, ""))
        # self.subtitle_app_thread.start()
        self.subtitle_window = subtitle_window
        self.is_generating = False
        self.output_colors = output_colors
        
    
    async def __aenter__(self):
        self.websocket = await self.websocket_object.__aenter__()
        return self
    
    # async def run_subtitle_window(self, font, font_size = 24, text = ""):
    #     self.subtitle_app = QApplication(sys.argv)
    #     self.subtitle_window = SubtitleWindow("", font, font_size)
    #     self.subtitle_app.exec()

    async def send_text(self, text, context_id, voice_settings = None):
        self.is_generating = True
        message = {
            "text": text,
            "context_id": context_id
        }

        if voice_settings:
            message["voice_settings"] = voice_settings

        await self.websocket.send(json.dumps(message))

    async def add_text(self, text, context_id):
        if not text:
            return
        await self.websocket.send(json.dumps({
            "text": text,
            "context_id": context_id
        }))

    async def flush(self, context_id):
        await self.websocket.send(json.dumps({
            "context_id": context_id,
            "flush": True
        }))

    async def interrupt(self, old_context_id, new_context_id, new_text):
        await self.websocket.send(json.dumps({
            "context_id": old_context_id,
            "close_context": True
        }))

        await self.send_text(new_text, new_context_id)

    async def end(self, context_id):
        await self.websocket.send(json.dumps({
            "close_socket": True,
            "context_id": context_id
        }))

        
    async def __aexit__(self, exc_type, exc, tb):
        await self.websocket_object.__aexit__(exc_type, exc, tb)

    async def process_alignment(self, new_alignment_list, force = False):
        """ Takes a list with alignment data by character and converts them by word, and then process the function """
        for char, start_time in new_alignment_list:
            if self.word_alignment:
                self.word_alignment[-1][0] += char
                if char == " ":
                    asyncio.create_task(self.schedule_word(self.word_alignment[-1][0], self.word_alignment[-1][1]))
                    self.word_alignment.append(["", self.time + start_time / 1000])
            else: 
                self.word_alignment.append([char, self.time + start_time / 1000])

        if force and self.word_alignment:
            asyncio.create_task(self.schedule_word(self.word_alignment[-1][0], self.word_alignment[-1][1]))
        
    # Adds and removes each word at time when they are said. 
    # text is going to be a word, likely with a space. 
    async def schedule_word(self, text, target_time):
        if target_time > time.time():
            await asyncio.sleep(target_time - time.time())
        self.current_words.append(text.strip())
        while sum([len(i) for i in self.current_words]) > self.max_character_in_subtitles and len(self.current_words) > 2:
            self.current_words = self.current_words[1:]
        self.subtitle_window.update_segments([(" ".join(self.current_words), self.output_colors[0], self.output_colors[1])])
        # print(text, end="", flush = True)
        # Potentially change this to have the array have a number with it

        # if self.current_words[0] == text.strip():
        #     self.current_words = self.current_words[1:]

    async def receive_messages(self):
        context_audio = {}

        try:
            async for message in self.websocket:
                data = json.loads(message)
                print("\n\n\n", flush = True)
                if data.get("isFinal"):
                    print(data, flush = True)
                    self.current_words.clear()
                    print("\nContext complete", flush = True)
                    self.is_generating = False
                    await self.queue_audio(data)
                if data.get("audio"):
                    await self.queue_audio(data)
                

        except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError):
            print("Message receiving stopped")

    async def queue_audio(self, data, force = False):
        # print("got audio")
        new_alignment_list = []
        if data.get("audio"):
            new_alignment_list = list(zip(data.get("alignment")["chars"], data.get("alignment")["charStartTimesMs"]))
            self.alignment += new_alignment_list
        # context_id = data.get("contextId", "default")
    
        if (self.audio_queued + len(self.audio_buffer_list) + 1 >= self.min_audio_before_playback) or data.get("isFinal"):
            audio_released_from_buffer = False
            for bytes in self.audio_buffer_list:
                # print("Chunk released from buffer", flush = True)
                self.audio_queued += 1
                audio_released_from_buffer = True
                if self.audio_queue.empty():
                    self.time = time.time()
                self.audio_queue.put(bytes)
            if audio_released_from_buffer:
                self.audio_buffer_list = []
                await self.process_alignment(self.alignment)
            if self.audio_queue.empty():
                self.time = time.time()
            # print("Directly queued chunk", flush = True)
            self.audio_queued += 1
            if data.get("audio"):
                self.audio_queue.put(self.decode_mp3_bytes(base64.b64decode(data.get("audio"))))
                await self.process_alignment(new_alignment_list, force = force)
        else:
            # print("Chunk Buffered", flush = True)
            if data.get("audio"):
                self.audio_buffer_list.append(self.decode_mp3_bytes(base64.b64decode(data.get("audio"))))
    
    # By ChatGPT
    # def decode_mp3_bytes(self, mp3_bytes):
    #     audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
    #     audio = audio.set_frame_rate(self.sample_rate).set_channels(self.channels)
    #     samples = np.array(audio.get_array_of_samples()).reshape(-1, self.channels)
    #     return samples.astype(np.float32) / (2**15)
    
    def decode_mp3_bytes(self, mp3_bytes):
        audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
        audio = audio.set_frame_rate(self.sample_rate).set_channels(self.channels)
        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        samples /= 32768.0  # Normalize
        if self.channels == 2:
            samples = samples.reshape(-1, 2)
        else:
            samples = samples.reshape(-1, 1)
        return samples
    
    # Also by ChatGPT
    # def audio_callback(self, outdata, frames, time, status):
    #     try:
    #         chunk = self.audio_queue.get_nowait()
    #         if chunk.shape[0] < frames:
    #             # Pad with zeros if chunk is too short
    #             padded = np.zeros((frames, self.channels), dtype=np.float32)
    #             padded[:chunk.shape[0]] = chunk
    #             outdata[:] = padded
    #         else:
    #             outdata[:] = chunk[:frames]
    #             remaining = chunk[frames:]
    #             if remaining.shape[0] > 0:
    #                 self.audio_queue.put_nowait(remaining)
    #     except queue.Empty:
    #         outdata[:] = np.zeros((frames, self.channels), dtype=np.float32)

    def audio_callback(self, outdata, frames, time, status):
        # Ensure enough samples in the buffer
        while len(self.internal_buffer) < frames:
            try:
                next_chunk = self.audio_queue.get_nowait()
                self.internal_buffer = np.vstack([self.internal_buffer, next_chunk])
            except queue.Empty:
                break

        if len(self.internal_buffer) >= frames:
            outdata[:] = self.internal_buffer[:frames]
            self.internal_buffer = self.internal_buffer[frames:]
        else:
            available = len(self.internal_buffer)
            outdata[:available] = self.internal_buffer
            outdata[available:] = 0.0  # Zero-fill remainder
            self.internal_buffer = np.zeros((0, self.channels), dtype=np.float32)
