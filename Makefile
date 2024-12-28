# Run server
run:
	@uvicorn server:app --host 0.0.0.0 --port 9000 --reload --log-level debug

test:
	@curl -X POST "http://127.0.0.1:9000/generate-speech" \
		-H "Content-Type: application/json" \
     	-d '{"text": "Hello, this is a test of the text-to-speech system."}' \
     	--output output.wav
