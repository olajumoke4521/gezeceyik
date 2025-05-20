from translate import Translator
from django.conf import settings

def translate_text_with_mymemory(text, target_lang_code, source_lang_code=None):
    if not text or not target_lang_code:
        return text

    if source_lang_code is None:
        source_lang_code = settings.MODELTRANSLATION_DEFAULT_LANGUAGE # 'en'

    if target_lang_code == source_lang_code:
        return text

    try:
        translator = Translator(to_lang=target_lang_code, from_lang=source_lang_code)
        translation = translator.translate(text)

        if translation.lower() == text.lower() and target_lang_code != source_lang_code:
            print(f"Warning: MyMemory might not have translated '{text}' to {target_lang_code}, returned original.")
        
        return translation
    except Exception as e:
        print(f"MyMemory Translation Error for text '{text[:50]}...' to {target_lang_code} from {source_lang_code}: {e}")
        return text