import logging
import assemblyai as aai
from elevenlabs import generate, stream
from openai import OpenAI

from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingClientOptions,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    BeginEvent,
    TurnEvent,
    TerminationEvent,
    StreamingError,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AI_Assistant:
    def __init__(self):
        self.assemblyai_api_key = "9e436fd4f862449ca0e00c90637be674"
        self.elevenlabs_api_key = "sk_522f2c0485daf97215e8b9349ea227d9c8b3a32e1e016c7a"

        self.openai_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key = "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"
            # api_key="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"
        )

        self.full_transcript = [
            {"role": "system", "content": "You are a receptionist at a dental clinic. Be resourceful and efficient."},
        ]

        self.goodbye_phrases = {"goodbye", "bye", "see you", "talk to you later", "thanks, bye", "thanks goodbye"}

        self.client = StreamingClient(
            StreamingClientOptions(api_key=self.assemblyai_api_key)
        )

        self.client.on(StreamingEvents.Begin, self.on_begin)
        self.client.on(StreamingEvents.Turn, self.on_turn)
        self.client.on(StreamingEvents.Termination, self.on_terminated)
        self.client.on(StreamingEvents.Error, self.on_error)

    def start_transcription(self):
        self.client.connect(
            StreamingParameters(
                sample_rate=16000,
                format_turns=True,
            )
        )

        try:
            print("[INFO] Starting microphone stream...")
            self.client.stream(
                aai.extras.MicrophoneStream(sample_rate=16000)
            )
        finally:
            self.client.disconnect(terminate=True)

    def stop_transcription(self):
        self.client.disconnect(terminate=True)

    def on_begin(self, _, event: BeginEvent):
        print(f"\n[INFO] Session started: {event.id}")

    def on_turn(self, client: StreamingClient, event: TurnEvent):
        if event.end_of_turn and event.transcript:
            if not event.turn_is_formatted:
                client.set_params(StreamingSessionParameters(format_turns=True))
            elif event.turn_is_formatted:
                transcript_text = event.transcript.strip()
                print(f"\n[FINAL TRANSCRIPT]: {transcript_text}")

                if self.is_goodbye(transcript_text):
                    self.end_conversation()
                else:
                    self.generate_ai_response(transcript_text)

    def on_terminated(self, _, event: TerminationEvent):
        print(f"\n[INFO] Session terminated. Duration: {event.audio_duration_seconds:.2f} seconds")

    def on_error(self, _, error: StreamingError):
        print(f"\n[ERROR] {error}")

    def generate_ai_response(self, transcript_text: str):
        try:
            self.full_transcript.append({"role": "user", "content": transcript_text})
            print(f"\nPatient: {transcript_text}")

            response = self.openai_client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324:free",
                messages=self.full_transcript
            )

            ai_response = response.choices[0].message.content
            self.full_transcript.append({"role": "assistant", "content": ai_response})
            print(f"\nAI Receptionist: {ai_response}")

            self.generate_audio(ai_response)

        except Exception as e:
            print(f"\n[ERROR] Failed to generate AI response: {e}")
            fallback = "I'm sorry, I encountered an error. Could you please repeat that?"
            self.generate_audio(fallback)

    def generate_audio(self, text):
        audio_stream = generate(
            api_key=self.elevenlabs_api_key,
            text=text,
            stream=True
        )
        stream(audio_stream)

    def is_goodbye(self, text: str) -> bool:
        return any(phrase in text.lower() for phrase in self.goodbye_phrases)

    def end_conversation(self):
        farewell = "Thank you for calling Vancouver Dental Clinic. Have a wonderful day. Goodbye!"
        print(f"\n[INFO] Ending conversation...")
        self.generate_audio(farewell)
        self.stop_transcription()


if __name__ == "__main__":
    greeting = "Thank you for calling Vancouver dental clinic. My name is Sandy, how may I assist you?"
    ai_assistant = AI_Assistant()
    ai_assistant.generate_audio(greeting)
    ai_assistant.start_transcription()
