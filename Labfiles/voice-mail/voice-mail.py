from dotenv import load_dotenv
import os
from playsound3 import playsound
import winsound
# Import namespaces from the Azure AI Projects SDK
from azure.identity import DefaultAzureCredential
import azure.cognitiveservices.speech as speechsdk
def main():
    try:
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')

        # Load Configuration from environment variables
        load_dotenv()
        foundry_endpoint = os.getenv("FOUNDARY_ENDPOINT")
        foundry_key = os.getenv("FOUNDARY_KEY")

        if foundry_key and foundry_key != "your_foundary_key_here":
            speech_config = speechsdk.SpeechConfig(
                subscription=foundry_key,
                endpoint=foundry_endpoint
            )
        else:
            credential = DefaultAzureCredential()
            speech_config = speechsdk.SpeechConfig(
                token_credential=credential,
                endpoint=foundry_endpoint
            )
        # Loop until user quits
        inputText = ""
        while inputText.lower() != "3":
            inputText = input("Enter an option: \n1: Record a greeting \n2: Transcribe message \n3: Exit \n ")
            if inputText != "3":
                if inputText == "1":
                    record_greeting(speech_config)
                elif inputText == "2":
                    transcribe_message(speech_config)
                elif inputText == "3":
                    print("Exiting...")
                    break
                else:
                    print("Invalid option. Please try again.")
    except Exception as e:
        print(f"Error: {e}")
# record a greeting using the microphone and save it to a file
def record_greeting(speech_config):
    print("Recording greeting... Press Ctrl+C to stop.")
    greeting_message = input("Enter your message: ")

    # Synthesize the greeting message to an audio file
    output_file = "greeting.wav"
    audio_config = speechsdk.audio.AudioOutputConfig(
        filename=output_file
    )
    speech_config.speech_synthesis_voice_name = "en-US-AvaNeural"

    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    result = speech_synthesizer.speak_text_async(greeting_message).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Greeting recorded and saved to {output_file}")
        # Play the WAV reliably on Windows
        winsound.PlaySound(output_file, winsound.SND_FILENAME)
        speech_synthesizer = None
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        print(f"Error details: {cancellation_details.error_details}")
    else:
        print(f"Error recording greeting: {result.reason}")
# transcribe_message function
def transcribe_message(speech_config):
    print("transcribe_message {speech_config}")
if __name__ == "__main__":
    main()