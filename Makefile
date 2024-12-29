# Run server
run:
	@uvicorn server:app --host 0.0.0.0 --port 9000

test:
	@curl -X POST "http://127.0.0.1:9000/generate-speech" \
		-H "Content-Type: application/json" \
     	-d '{"text": "Hello, this is a test of the text to speech system."}' \
     	--output output.wav

test-numbers:
	@curl -X POST "http://127.0.0.1:9000/generate-speech" \
		-H "Content-Type: application/json" \
     	-d '{ "text": "32 is a number. 32.5 is a number with more precision." }' \
     	--output output.wav


test-with-effects:
	@curl -X POST "http://127.0.0.1:9000/generate-speech" \
		-H "Content-Type: application/json" \
     	-d '{ "reverb_room_size": 0.35, "text": "Hello, this is a test of the text to speech system." }' \
     	--output output.wav
