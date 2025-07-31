from RealtimeSTT import AudioToTextRecorder

class STTManager:
    def __init__(self, config = {
        'spinner': True,
        'model': 'small.en', # or large-v2 or deepdml/faster-whisper-large-v3-turbo-ct2 or ...
        'download_root': None, # default download root location. Ex. ~/.cache/huggingface/hub/ in Linux
        # 'input_device_index': 1,
        'realtime_model_type': 'small.en', # or small.en or distil-small.en or ...
        'language': 'en',
        'silero_sensitivity': 0.05,
        'webrtc_sensitivity': 3,
        'post_speech_silence_duration': 0.7,
        'min_length_of_recording': 1.1,        
        'min_gap_between_recordings': 0,                
        'enable_realtime_transcription': True,
        'realtime_processing_pause': 0.02,
        'on_realtime_transcription_update': None,
        'use_main_model_for_realtime': True,
        'handle_buffer_overflow': False,
        #'on_realtime_transcription_stabilized': text_detected,
        'silero_deactivity_detection': True,
        'early_transcription_on_silence': 0,
        'beam_size': 5,
        'beam_size_realtime': 3,
        # 'batch_size': 0,
        # 'realtime_batch_size': 0,        
        'no_log_file': True,
        'initial_prompt_realtime': (
            "End incomplete sentences with ellipses.\n"
            "Examples:\n"
            "Complete: The sky is blue.\n"
            "Incomplete: When the sky...\n"
            "Complete: She walked home.\n"
            "Incomplete: Because he...\n"
        ),
        'silero_use_onnx': True,
        'faster_whisper_vad_filter': True,
        'ensure_sentence_ends_with_period': False,
    }):
        self.config = config
        if not self.config['on_realtime_transcription_update']:
            self.config['on_realtime_transcription_update'] = self.process_text
        self.recorder = AudioToTextRecorder(**config)
        self.prev_text = ""
        self.ready_to_send = False
        self.current_text = ""

    def process_text(self, text):
        text = text.lstrip()
        if text.startswith("..."):
            text = text[3:]
        text = text.lstrip()
        if text:
            text = text[0].upper() + text[1:]
        sentence_end_marks = ['.', '!', '?', '。'] 
        if text.endswith("..."):
            self.recorder.post_speech_silence_duration = 2.0
        elif text and text[-1] in sentence_end_marks and self.prev_text and self.prev_text[-1] in sentence_end_marks:
            self.recorder.post_speech_silence_duration = 0.45
        else:
            self.recorder.post_speech_silence_duration = 0.7

        self.prev_text = text

        text = text.rstrip()
        if text.endswith("..."):
            text = text[:-2]
                
        if not text:
            return
        self.prev_text = ""
        
        return text
    
    def append_text(self, text):
        self.current_text += text + " "
    
    def send_text_to_function(self, process_function):
        self.recorder.text(process_function)

    def shutdown(self):
        self.recorder.shutdown()





    



