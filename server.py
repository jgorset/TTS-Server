import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import SpeechT5HifiGan, SpeechT5Processor, SpeechT5ForTextToSpeech
from datasets import load_dataset
import torch
import numpy as np
from io import BytesIO
from fastapi.responses import StreamingResponse
from pedalboard import Pedalboard, PitchShift, Reverb, Delay, Chorus, Distortion, LowpassFilter, HighpassFilter

# Define the FastAPI app
debug = os.environ.get("DEBUG", False) == "true"

app = FastAPI(debug=debug)

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preload the model and resources
try:
    processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
    model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to("cuda")
    vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to("cuda")
    embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
    speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0).to("cuda")
except Exception as e:
    raise RuntimeError(f"Failed to load model or resources: {e}")

# Request schema
class TextToSpeechRequest(BaseModel):
    text: str
    pitch_shift_semitones: int = 0  # Default no pitch shift
    reverb_room_size: float = 0.0  # Default room size
    reverb_damping: float = 0.0  # Default damping
    delay_seconds: float = 0.0  # Default no delay
    chorus_rate: float = 0.0  # Default no chorus
    distortion_gain_db: float = 0.0  # Default no distortion
    lowpass_cutoff: float = 0.0  # Default no lowpass filter
    highpass_cutoff: float = 0.0  # Default no highpass filter

@app.post("/generate-speech")
async def generate_speech_endpoint(request: TextToSpeechRequest):
    text = request.text

    if not text:
        raise HTTPException(status_code=400, detail="Text input is required.")

    try:
        # Prepare inputs
        inputs = processor(text=text, return_tensors="pt").to("cuda")

        # Generate speech
        speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)

        # Convert the tensor to a NumPy array on the CPU
        speech_np = speech.cpu().numpy()

        # Scale to float32 for optional Pedalboard processing
        speech_float32 = speech_np.astype(np.float32)

        # Add padding for effects tails
        max_tail_duration = max(request.delay_seconds, request.reverb_room_size * 2)  # Estimate reverb tail length
        padding_samples = int(max_tail_duration * 16000)  # Assuming a sample rate of 16 kHz
        speech_float32 = np.pad(speech_float32, (0, padding_samples), mode='constant')

        effects = []

        if request.pitch_shift_semitones != 0:
            effects.append(PitchShift(semitones=request.pitch_shift_semitones))

        if request.reverb_room_size > 0 or request.reverb_damping > 0:
            effects.append(Reverb(room_size=request.reverb_room_size, damping=request.reverb_damping))

        if request.delay_seconds > 0:
            effects.append(Delay(delay_seconds=request.delay_seconds))

        if request.chorus_rate > 0:
            effects.append(Chorus(rate_hz=request.chorus_rate))

        if request.distortion_gain_db > 0:
            effects.append(Distortion(gain_db=request.distortion_gain_db))

        if request.lowpass_cutoff > 0:
            effects.append(LowpassFilter(cutoff_frequency_hz=request.lowpass_cutoff))

        if request.highpass_cutoff > 0:
            effects.append(HighpassFilter(cutoff_frequency_hz=request.highpass_cutoff))

        if effects:
            board = Pedalboard(effects)
            processed_audio = board.process(speech_float32, sample_rate=16000)
        else:
            processed_audio = speech_float32

        # Normalize the audio to the maximum range without clipping
        max_amplitude = np.max(np.abs(processed_audio))
        if max_amplitude > 0:
            processed_audio = processed_audio / max_amplitude
            
        # Trim silence from the end (if necessary)
        threshold = 0.0001  # Adjust threshold as needed
        end_index = len(processed_audio)
        for i in reversed(range(len(processed_audio))):
            if abs(processed_audio[i]) > threshold:
                end_index = i + 1
                break

        processed_audio = processed_audio[:end_index]

        # Convert back to int16 for WAV format
        processed_audio_int16 = (processed_audio * 32767).astype(np.int16)

        # Create a WAV file in memory
        buffer = BytesIO()
        from scipy.io.wavfile import write
        write(buffer, rate=16000, data=processed_audio_int16)
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="audio/wav")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {e}")

@app.get("/")
def root():
    return {"message": "Text-to-Speech API is running."}
