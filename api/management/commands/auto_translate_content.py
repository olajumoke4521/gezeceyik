import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from api.models import Place, Category, ExpectationDefinition, SortTagDefinition  # Your parler models
from api.utils import translate_text_with_mymemory


class Command(BaseCommand):
    help = 'Attempts to automatically translate untranslated content for specified models using MyMemory (adapted for django-parler).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--models',
            nargs='+',
            type=str.lower,
            default=['place', 'category', 'expectationdefinition', 'sorttagdefinition'],
            help='Specify which models to translate (e.g., place category). Default: all configured.',
        )
        parser.add_argument(
            '--languages',
            nargs='+',
            type=str,
            help='Specify target language codes to translate (e.g., tr ru). Default: all except source.',
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update existing translations. Default: only translates empty fields.',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.1,
            help='Delay in seconds between translation API calls to respect rate limits.',
        )
        parser.add_argument(
            '--source-lang',
            type=str,
            default=settings.LANGUAGE_CODE,  # Use Django's default language setting
            help=f'Source language code (default: {settings.LANGUAGE_CODE})',
        )
        parser.add_argument(
            '--pks',
            nargs='+',
            type=int,
            help='Translate only specific primary keys for the given models.',
        )

    def handle(self, *args, **options):
        source_language = options['source_lang']
        target_languages_input = options['languages']
        if target_languages_input:
            valid_target_languages = [
                lc for lc in target_languages_input
                if lc != source_language and lc in [code for code, _ in settings.LANGUAGES]
            ]
            if not valid_target_languages:
                raise CommandError(
                    f"No valid target languages specified or all are source language. Check settings.LANGUAGES."
                )
        else:
            valid_target_languages = [code for code, name in settings.LANGUAGES if code != source_language]

        force_update = options['force_update']
        api_delay = options['delay']
        pks_to_translate = options.get('pks')

        # Config for parler models
        models_config = {
            'category': {'model_class': Category, 'text_fields': ['name']},
            'place': {'model_class': Place, 'text_fields': ['name', 'description']},
            'expectationdefinition': {'model_class': ExpectationDefinition, 'text_fields': ['name']},
            'sorttagdefinition': {'model_class': SortTagDefinition, 'text_fields': ['name']},
        }

        models_to_translate_input = options['models']

        self.stdout.write(f"Source language: {source_language}")
        self.stdout.write(f"Target languages: {', '.join(valid_target_languages)}")
        self.stdout.write(f"Force update: {force_update}")
        self.stdout.write(f"API call delay: {api_delay}s")
        self.stdout.write(f"Models to translate: {', '.join(models_to_translate_input)}")
        if pks_to_translate:
            self.stdout.write(f"Specific PKs to translate: {', '.join(map(str, pks_to_translate))}")

        total_api_calls = 0
        total_saves = 0

        for model_key in models_to_translate_input:
            if model_key not in models_config:
                self.stdout.write(self.style.WARNING(f"Skipping unknown model '{model_key}'."))
                continue

            config = models_config[model_key]
            ModelClass = config['model_class']
            fields_to_translate = config['text_fields']

            self.stdout.write(self.style.HTTP_INFO(f"\n--- Translating {ModelClass._meta.verbose_name_plural} ---"))

            queryset = ModelClass.objects.all()
            if pks_to_translate:
                queryset = queryset.filter(pk__in=pks_to_translate)

            for instance in queryset:
                item_identifier_text = instance.safe_translation_getter(
                    fields_to_translate[0], language_code=source_language, any_language=True
                ) or f"PK: {instance.pk}"
                item_identifier = f"{ModelClass._meta.verbose_name} '{item_identifier_text[:30]}...' (ID: {instance.pk})"

                instance_needs_saving = False

                for field_name in fields_to_translate:
                    instance.set_current_language(source_language)
                    source_text = getattr(instance, field_name, None)

                    if not source_text or not str(source_text).strip():
                        self.stdout.write(
                            f"  Skipping {item_identifier} field '{field_name}': no source text in '{source_language}'.")
                        continue

                    for lang_code in valid_target_languages:
                        instance.set_current_language(lang_code)
                        current_translation = getattr(instance, field_name, None)

                        if force_update or not current_translation or not str(current_translation).strip():
                            self.stdout.write(
                                f"  Translating {item_identifier} field '{field_name}' from '{source_language}' to '{lang_code}'...")
                            total_api_calls += 1

                            translated_text = translate_text_with_mymemory(source_text, lang_code, source_language)

                            if translated_text and translated_text.strip().lower() != source_text.strip().lower():
                                setattr(instance, field_name,
                                        translated_text)
                                instance_needs_saving = True
                                self.stdout.write(f"    -> '{translated_text[:70]}...'")
                            elif translated_text:
                                self.stdout.write(
                                    f"    -> No change, same as source, or API returned empty for '{field_name}' to {lang_code}.")
                            else:
                                self.stdout.write(
                                    self.style.ERROR(f"    -> Translation FAILED for '{field_name}' to {lang_code}."))


                            if total_api_calls > 0:
                                time.sleep(api_delay)
                        else:
                            self.stdout.write(
                                f"  Skipping {item_identifier} field '{field_name}' for {lang_code} (already translated and non-empty).")

                if instance_needs_saving:
                    try:
                        instance.save()
                        total_saves += 1
                        self.stdout.write(self.style.SUCCESS(f"  Saved translations for {item_identifier}"))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"  Error saving {item_identifier}: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f'\nFinished auto-translation attempt. API Calls: {total_api_calls}, Saves: {total_saves}'))