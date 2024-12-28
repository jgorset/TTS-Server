# TTS-Server

## Overview

**TTS-Server** is a lightweigh Text-to-Speech (TTS) server that leverages cutting-edge AI models for natural-sounding speech synthesis.

---

## Features

- **High-Quality TTS**: Powered by Microsoft's SpeechT5 models for text-to-speech generation.
- **Audio Effects (Optional)**: Apply pitch shifting and reverb using Pedalboard for enhanced audio processing.
- **GPU Support**: Offloads intensive computations to GPU for improved performance.

---

## Requirements

- Python 3.8+
- CUDA-compatible GPU (for optimal performance)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jgorset/tts-server.git
   cd tts-server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install `Pedalboard` if you plan to use audio effects:
   ```bash
   pip install pedalboard
   ```

---

## Configuration

### Environment Variables

| Variable                  | Default     | Description                                   |
|---------------------------|-------------|-----------------------------------------------|
| `PROCESS_SOUND`           | `false`     | Enable audio processing (e.g., pitch/reverb). |
| `PITCH_SHIFT_SEMITONES`   | `0`         | Pitch shift semitones (integer).             |
| `REVERB_ROOM_SIZE`        | `0.35`      | Room size for reverb (float).                |
| `REVERB_DAMPING`          | `0.5`       | Damping factor for reverb (float).           |

---

## Usage

### Starting the Server

Run the server using:
```bash
make run
```

### API Endpoints

#### Health Check
- **Endpoint**: `GET /`
- **Response**:
  ```json
  {
    "message": "Text-to-Speech API is running."
  }
  ```

#### Generate Speech
- **Endpoint**: `POST /generate-speech`
- **Request Body**:
  ```json
  {
    "text": "Hello, world!"
  }
  ```
- **Response**: Returns a WAV audio file as a streaming response.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/generate-speech" \
       -H "Content-Type: application/json" \
       -d '{"text": "Hello, world!"}' --output output.wav
  ```

---

## Optional Audio Effects

Enable audio processing by setting `PROCESS_SOUND=true` in the environment. Effects include:

1. **Pitch Shift**: Adjusts the pitch of the audio by the specified semitones.
2. **Reverb**: Adds a reverberation effect with configurable room size and damping.

---

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your improvements.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Acknowledgments

- [Hugging Face](https://huggingface.co/) for providing the SpeechT5 models.
- [Spotify](https://github.com/spotify/pedalboard) for the Pedalboard library.
