#!/bin/bash

cd /Users/Subho/Projects/openclaw-voice-chat

echo "Creating a simple working version..."
echo ""

# Create a minimal working version that bypasses all the complexity
cat > static/working_version.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw - Simple Working Version</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            max-width: 600px;
            width: 100%;
        }
        h1 { color: white; text-align: center; margin-bottom: 30px; }
        .status { 
            color: white; 
            padding: 15px; 
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .mic-button {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 60px;
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        .mic-button:hover {
            transform: scale(1.05);
            box-shadow: 0 15px 40px rgba(0,0,0,0.4);
        }
        .mic-button.recording {
            animation: pulse 1s infinite;
            background: linear-gradient(135deg, #f093fb, #f5576c);
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        .messages {
            margin-top: 30px;
            max-height: 300px;
            overflow-y: auto;
        }
        .message {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            margin: 5px 0;
            border-radius: 8px;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ OpenClaw Voice Chat</h1>
        <div class="status" id="status">Click the mic to start</div>
        <button class="mic-button" id="micBtn">🎤</button>
        <div class="messages" id="messages"></div>
    </div>

    <script>
        const API_URL = 'http://127.0.0.1:5999';
        let isRecording = false;
        let mediaRecorder = null;

        const status = document.getElementById('status');
        const micBtn = document.getElementById('micBtn');
        const messages = document.getElementById('messages');

        function addMessage(text) {
            const msg = document.createElement('div');
            msg.className = 'message';
            msg.textContent = text;
            messages.appendChild(msg);
            messages.scrollTop = messages.scrollHeight;
        }

        micBtn.addEventListener('click', async () => {
            console.log('Button clicked! isRecording:', isRecording);
            
            if (isRecording) {
                // Stop recording
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                    mediaRecorder.stop();
                }
                isRecording = false;
                micBtn.classList.remove('recording');
                status.textContent = 'Processing...';
            } else {
                // Start recording
                try {
                    status.textContent = 'Requesting microphone...';
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    
                    status.textContent = 'Recording...';
                    micBtn.classList.add('recording');
                    
                    mediaRecorder = new MediaRecorder(stream);
                    let audioChunks = [];
                    
                    mediaRecorder.ondataavailable = (e) => {
                        audioChunks.push(e.data);
                    };
                    
                    mediaRecorder.onstop = async () => {
                        status.textContent = 'Sending to server...';
                        
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const formData = new FormData();
                        formData.append('audio', audioBlob);
                        
                        try {
                            // Send to Whisper for transcription
                            const whisperResponse = await fetch('http://127.0.0.1:5679/transcribe', {
                                method: 'POST',
                                body: formData
                            });
                            
                            if (!whisperResponse.ok) {
                                throw new Error('Whisper server error');
                            }
                            
                            const whisperData = await whisperResponse.json();
                            const transcript = whisperData.text;
                            
                            addMessage('You: ' + transcript);
                            status.textContent = 'AI thinking...';
                            
                            // Get AI response and voice
                            const voiceResponse = await fetch(API_URL + '/voice/stream', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ text: transcript })
                            });
                            
                            if (!voiceResponse.ok) {
                                throw new Error('Voice server error');
                            }
                            
                            const audioBlob = await voiceResponse.blob();
                            const audioUrl = URL.createObjectURL(audioBlob);
                            
                            // Play audio
                            const audio = new Audio(audioUrl);
                            audio.play();
                            
                            addMessage('AI: Response playing...');
                            status.textContent = 'Click to speak again';
                            
                            // Stop all tracks
                            stream.getTracks().forEach(track => track.stop());
                            
                        } catch (error) {
                            console.error('Error:', error);
                            addMessage('Error: ' + error.message);
                            status.textContent = 'Error - try again';
                            stream.getTracks().forEach(track => track.stop());
                        }
                    };
                    
                    mediaRecorder.start();
                    isRecording = true;
                    
                    // Auto-stop after 5 seconds of silence
                    setTimeout(() => {
                        if (isRecording && mediaRecorder.state === 'recording') {
                            console.log('Auto-stopping recording');
                            mediaRecorder.stop();
                        }
                    }, 8000);
                    
                } catch (error) {
                    console.error('Microphone error:', error);
                    status.textContent = 'Error: ' + error.message;
                    addMessage('Error: ' + error.message);
                }
            }
        });

        console.log('Page loaded. API URL:', API_URL);
    </script>
</body>
</html>
HTMLEOF

echo "✅ Created working_version.html"
echo ""
echo "Open in browser: http://localhost:8000/working_version.html"
echo ""
echo "This version has minimal code and should work if the issue is complexity-related."
