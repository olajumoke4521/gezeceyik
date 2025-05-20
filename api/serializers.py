from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import (
    Language, Category, Place, PlaceImage, OpeningHour,
    ExpectationDefinition, SortTagDefinition
)
from django.utils.translation import get_language, activate 
from parler_rest.serializers import TranslatableModelSerializer, TranslatedFieldsField
from parler_rest.fields import TranslatedField

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['code', 'name', 'flag_icon_key']

class CategorySerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Category)

    class Meta:
        model = Category
        fields = ['id', 'name', 'icon_key']

class PlaceImageSerializer(serializers.ModelSerializer): 
    class Meta:
        model = PlaceImage
        fields = ['image_url', 'order']

class OpeningHourSerializer(serializers.ModelSerializer): 
    day = serializers.CharField(source='get_day_of_week_display')
    open = serializers.TimeField(source='open_time', format='%H:%M')
    close = serializers.TimeField(source='close_time', format='%H:%M')

    class Meta:
        model = OpeningHour
        fields = ['day', 'open', 'close']

class ExpectationDefinitionSerializer(TranslatableModelSerializer):
    name = TranslatedField()

    class Meta:
        model = ExpectationDefinition
        fields = ['key', 'icon_key', 'name']

class SortTagDefinitionSerializer(TranslatableModelSerializer):
    name = TranslatedField()

    class Meta:
        model = SortTagDefinition
        fields = ['key', 'icon_key', 'type', 'name']

class PlaceListSerializer(TranslatableModelSerializer):
    name = TranslatedField()
    description = TranslatedField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    working_hours_status = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = [
            'id', 'name', 'description', 'category', 
            'category_name', 'main_image',
            'latitude', 'longitude', 'working_hours_status',

        ]

    def get_working_hours_status(self, obj):
        return obj.get_working_hours_status()


class PlaceDetailSerializer(TranslatableModelSerializer):
    all_translations = TranslatedFieldsField(shared_model=Place, source='translations', read_only=True)

    type = serializers.CharField(source='category.name', read_only=True)
    location = serializers.SerializerMethodField()
    images = PlaceImageSerializer(many=True, read_only=True)
    open_times = OpeningHourSerializer(source='open_times.all', many=True, read_only=True)
    expectations = serializers.SerializerMethodField()
    sorting_tags = serializers.SerializerMethodField()
    working_hours_status = serializers.SerializerMethodField()
    contact_information = serializers.SerializerMethodField()
    social_medias = serializers.SerializerMethodField() 
    icon_keys_for_contact = serializers.SerializerMethodField()
    user_interaction = serializers.SerializerMethodField()

    # Caches for definitions to optimize queries
    _expectation_definitions_cache = None
    _sort_tag_definitions_cache = None

    class Meta:
        model = Place
        fields = [
            'id', 'type', 'name', 'description', 'all_translations',
            'address', 'location', 'main_image', 'images', 'working_hours_status',
            'open_times', 'contact_information', 'social_medias', 'icon_keys_for_contact',
            'user_interaction',
            'expectations', 
            'sorting_tags',
        ]
    def _get_all_expectation_definitions(self):
        current_lang_for_debug = get_language()

        # Fetch all master objects first
        all_master_definitions = ExpectationDefinition.objects.all()

        temp_cache = {}
        for defn_master in all_master_definitions:
            defn_master.set_current_language(current_lang_for_debug)
            temp_cache[defn_master.key] = defn_master

        self._expectation_definitions_cache = temp_cache

        return self._expectation_definitions_cache

    def _get_all_sort_tag_definitions(self):
        current_lang_for_debug = get_language()

        all_master_definitions = SortTagDefinition.objects.all()

        temp_cache = {}
        for defn_master in all_master_definitions:
            defn_master.set_current_language(current_lang_for_debug)

            temp_cache[defn_master.key] = defn_master

        self._sort_tag_definitions_cache = temp_cache
        return self._sort_tag_definitions_cache
    
    
    def get_location(self, obj):
        return {
            "latitude": str(obj.latitude) if obj.latitude is not None else None,
            "longitude": str(obj.longitude) if obj.longitude is not None else None
        }

    def get_working_hours_status(self, obj):
        return obj.get_working_hours_status() 

    def get_expectations(self, obj):
        field_to_key_map = { 
            "outside_area": "outsideArea", "inside_area": "insideArea",
            "kard_pay": "kardPay", "kids_menu": "kidsMenu", "baby_sit": "babySit",
            "free_park_area": "freeParkArea", "wheelchair_accessible_entrance": "WheelchairAccessibleEntrance",
            "pets_allow": "petsAllow",
            "reservation": "reservation", "cash": "cash", "bar": "bar",
            "coffee": "coffee", "alcohol": "alcohol",
            "dessert": "dessert", "kitchen": "kitchen", "fish": "fish",
            "meat_and_chicken": "meatAndChicken"
        }
        all_definitions = self._get_all_expectation_definitions()
        display_list = []

        for model_field, definition_key in field_to_key_map.items():
            is_true = getattr(obj, model_field, False)
            if is_true:
                definition_obj = all_definitions.get(definition_key)
                item_data = {
                    definition_key: True,
                    # 'name' from definition_obj will be in the current language
                    "label": definition_obj.name if definition_obj else definition_key.title(),
                    "icon_key": definition_obj.icon_key if definition_obj else None
                }
                if not definition_obj:
                    print(
                        f"Warning: ExpectationDefinition not found for key: {definition_key}. Using default label for {model_field}.")
                display_list.append(item_data)
        return display_list

    def get_sorting_tags(self, obj):
        field_to_key_map = {
            "popular": "popular", "historical_places": "historicalPlaces", "alcohol": "alcohol",
            "beach": "beach", "coffee": "coffee",  # Assuming this 'coffee' is for sorting_tags
            "creative_places": "creativePlaces", "castles": "castles",
            "museum": "museum", "parks": "parks", "waterfalls": "waterfalls",
            "hiking_trails": "hikingTrails",
            "kyrenia": "kyrenia", "nicosia": "nicosia", "famagusta": "famagusta",
            "iskele": "iskele", "guzelyurt": "guzelyurt", "karpaz": "karpaz", "lefke": "lefke"
        }
        all_definitions = self._get_all_sort_tag_definitions()
        display_list = []
        for model_field, definition_key in field_to_key_map.items():
            is_true = getattr(obj, model_field, False)
            if is_true:
                definition_obj = all_definitions.get(definition_key)
                item_data = {
                    definition_key: True,
                    # 'name' from definition_obj will be in the current language
                    "label": definition_obj.name if definition_obj else definition_key.title(),
                    "icon_key": definition_obj.icon_key if definition_obj else None
                }
                if not definition_obj:
                    print(
                        f"Warning: SortTagDefinition not found for key: {definition_key}. Using default label for {model_field}.")
                display_list.append(item_data)
        return display_list

    def get_contact_information(self, obj): 
        return {
            "phone": obj.phone, 
            "website": obj.website, 
            "email": obj.email, 
            "map_link": obj.map_link, 
            "whatsapp": obj.whatsapp
            }
    def get_social_medias(self, obj): 
        return {
            "instagram": obj.instagram, 
            "twitter": obj.twitter, 
            "facebook": obj.facebook, 
            "pinterest": obj.pinterest
            }
    
    def get_icon_keys_for_contact(self, obj): 
        return {
            "phone": "phone", 
            "website": "website", 
            "mail": "mail", 
            "location": "location",
            "whatsapp": "whatsapp", 
            "instagram": "instagram", 
            "facebook": "facebook", 
            "twitter": "twitter", 
            "pinterest": "pinterest"
            }
    
    def get_user_interaction(self, obj):
        request = self.context.get('request')
        device_id = None
        if request:
            if request.method == 'POST' and hasattr(request, 'data'):
                device_id = request.data.get('device_id')
            elif hasattr(request, 'GET'):
                device_id = request.GET.get('device_id')

        is_liked = False
        if device_id and device_id in obj.liked_by_devices:
            is_liked = True
        return {"is_liked": is_liked}


class WheelSpinRequestSerializer(serializers.Serializer): 
    region_keys = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    expectation_keys = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    category_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    device_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class LikeRequestSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True)
    