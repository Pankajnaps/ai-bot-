'''
+-------------------+        +-----------------------+        +------------------+        +------------------------+
|   Step 1: Install |        |  Step 2: Real-Time    |        |  Step 3: Pass    |        |  Step 4: Live Audio    |
|   Python Libraries|        |  Transcription with   |        |  Real-Time       |        |  Stream from ElevenLabs|
+-------------------+        |       AssemblyAI      |        |  Transcript to   |        |                        |
|                   |        +-----------------------+        |      OpenAI      |        +------------------------+
| - assemblyai      |                    |                    +------------------+                    |
| - openai          |                    |                             |                              |
| - elevenlabs      |                    v                             v                              v
| - mpv             |        +-----------------------+        +------------------+        +------------------------+
| - portaudio       |        |                       |        |                  |        |                        |
+-------------------+        |  AssemblyAI performs  |-------->  OpenAI generates|-------->  ElevenLabs streams   |
                             |  real-time speech-to- |        |  response based  |        |  response as live      |
                             |  text transcription   |        |  on transcription|        |  audio to the user     |
                             |                       |        |                  |        |                        |
                             +-----------------------+        +------------------+        +------------------------+

###### Step 1: Install Python libraries ######

brew install portaudio
pip install "assemblyai[extras]"
pip install elevenlabs==0.3.0b0
brew install mpv
pip install --upgrade openai
'''

import assemblyai as aai
from elevenlabs import generate, stream
from openai import OpenAI

class AI_Assistant:
    def __init__(self):
        # ASSEMBLYAI-API-KEY
        aai.settings.api_key = "9e436fd4f862449ca0e00c90637be674"
        # self.openai_client = OpenAI(api_key = "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")
        self.elevenlabs_api_key = "sk_522f2c0485daf97215e8b9349ea227d9c8b3a32e1e016c7a"
        # base_url = "https://openrouter.ai/api/v1"

        self.transcriber = None
        self.openai_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key="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"
            )

        # Prompt
        self.full_transcript = [
            {"role":"system", "content":"You are a receptionist at a dental clinic. Be resourceful and efficient."},
        ]

###### Step 2: Real-Time Transcription with AssemblyAI ######
        
    def start_transcription(self):
        self.transcriber = aai.RealtimeTranscriber(
            sample_rate = 16000,
            on_data = self.on_data,
            on_error = self.on_error,
            on_open = self.on_open,
            on_close = self.on_close,
            end_utterance_silence_threshold = 1000
        )

        self.transcriber.connect()
        microphone_stream = aai.extras.MicrophoneStream(sample_rate =16000)
        self.transcriber.stream(microphone_stream)
    
    def stop_transcription(self):
        if self.transcriber:
            self.transcriber.close()
            self.transcriber = None

    def on_open(self, session_opened: aai.RealtimeSessionOpened):
        print("Session ID:", session_opened.session_id)
        return


    def on_data(self, transcript: aai.RealtimeTranscript):
        if not transcript.text:
            return

        if isinstance(transcript, aai.RealtimeFinalTranscript):
            self.generate_ai_response(transcript)
        else:
            print(transcript.text, end="\r")


    def on_error(self, error: aai.RealtimeError):
        print("An error occured:", error)
        return


    def on_close(self):
        #print("Closing Session")
        return

###### Step 3: Pass real-time transcript to OpenAI ######
    
    # def generate_ai_response(self, transcript):

    #     self.stop_transcription()

    #     self.full_transcript.append({"role":"user", "content": transcript.text})
    #     print(f"\nPatient: {transcript.text}", end="\r\n")

    #     response = self.openai_client.chat.completions.create(
    #         model = "gpt-3.5-turbo",
    #         messages = self.full_transcript
    #     )

    #     ai_response = response.choices[0].message.content

    #     self.generate_audio(ai_response)

    #     self.start_transcription()
    #     print(f"\nReal-time transcription: ", end="\r\n")
    def generate_ai_response(self, transcript):

        self.stop_transcription()

        self.full_transcript.append({"role": "user", "content": transcript.text})
        print(f"\nPatient: {transcript.text}", end="\r\n")

        response = self.openai_client.chat.completions.create(
            model="deepseek/deepseek-chat:free",
            messages=self.full_transcript
        )

        ai_response = response.choices[0].message.content

        self.generate_audio(ai_response)

        self.start_transcription()
        print(f"\nReal-time transcription: ", end="\r\n")



###### Step 4: Generate audio with ElevenLabs ######
        
    def generate_audio(self, text):

        self.full_transcript.append({"role":"assistant", "content": text})
        print(f"\nAI Receptionist: {text}")

        audio_stream = generate(
            api_key = self.elevenlabs_api_key,
            text = text,
            # voice = "Rachel",
            stream = True
        )

        stream(audio_stream)

greeting = "Thank you for calling Vancouver dental clinic. My name is Sandy, how may I assist you?"
ai_assistant = AI_Assistant()
# ai_assistant.generate_audio(greeting)
ai_assistant.start_transcription()

        





    



    




