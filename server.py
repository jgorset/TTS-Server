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

# Environment configuration
USE_PEDALBOARD = os.environ.get("PROCESS_SOUND", "false").lower() == "true"

if USE_PEDALBOARD:
    from pedalboard import Pedalboard, PitchShift, Reverb

    PITCH_SHIFT_SEMITONES = int(os.environ.get("PITCH_SHIFT_SEMITONES", 0))
    REVERB_ROOM_SIZE = float(os.environ.get("REVERB_ROOM_SIZE", 0.35))
    REVERB_DAMPING = float(os.environ.get("REVERB_DAMPING", 0.5))

# Define the FastAPI app
app = FastAPI()

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

        if USE_PEDALBOARD:
            # Apply effects using Pedalboard
            board = Pedalboard([
                PitchShift(semitones=PITCH_SHIFT_SEMITONES),
                Reverb(room_size=REVERB_ROOM_SIZE, damping=REVERB_DAMPING),
            ])
            processed_audio = board.process(speech_float32, sample_rate=16000)
        else:
            processed_audio = speech_float32

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
