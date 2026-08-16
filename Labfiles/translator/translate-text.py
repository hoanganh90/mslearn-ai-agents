from dotenv import load_dotenv
import os
import sys
from playsound3 import playsound
import winsound
# Import namespaces from the Azure AI Projects SDK
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient

def main():
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        # Clear the console
        os.system('cls' if os.name == 'nt' else 'clear')
        # Get configuration Settings
        load_dotenv()
        foundry_endpoint = os.getenv("MODEL_ENDPOINT")
        text_translation_endpoint = os.getenv("MODEL_ENDPOINT")
        text_translation_key = os.getenv("MODEL_KEY")
        region = os.getenv("MODEL_REGION", "swedencentral")

        # Create client using endpoint and credential
        credential = AzureKeyCredential(text_translation_key) if text_translation_key else DefaultAzureCredential()
        client = TextTranslationClient(
            endpoint=text_translation_endpoint, 
            credential=credential, 
            region=region
        )

        # Choose target language
        languageResponse = client.get_supported_languages(scope="translation")
        supported_languages = languageResponse.translation
        
        # Print list of supported languages
        print("Supported languages:")
        for code, lang in supported_languages.items():
            print(f"  {lang.name} ({code})")
        print("Enter target language code (e.g., es, fr, de, it, ja): ")
        target_language = input()
        if target_language not in supported_languages:
            print("Invalid language code. Please try again.")
            return
        
        # Translate
        inputText = ""
        while inputText.lower() != "quit":
            inputText = input("\nEnter text to translate ('quit' to exit): ")
            if inputText.lower() != "quit":
                text = [inputText]
                translationResponse = client.translate(body=text, to_language=[target_language])
                translation = translationResponse[0] if translationResponse else None
                if translation:
                    sourceLanguage = translation.detected_language.language if translation.detected_language else "unknown"
                    for translated_text in translation.translations:
                        print(f"\nSource ({sourceLanguage}):")
                        print(inputText)
                        target_lang_code = getattr(translated_text, 'to', getattr(translated_text, 'language', target_language))
                        print(f"\nTranslated ({target_lang_code}):")
                        print(translated_text.text)
    except Exception as ex:
        print(ex)

if __name__ == "__main__":
    main()