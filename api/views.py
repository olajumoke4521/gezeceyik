from rest_framework import viewsets, generics, status, views
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
import random
from django.db import models
from django.conf import settings 
from rest_framework import viewsets, filters 
from django_filters.rest_framework import DjangoFilterBackend 
from .filters import PlaceFilter

from .models import (
    Language, Category, Place, ExpectationDefinition, SortTagDefinition
)
from .serializers import (
    LanguageSerializer, CategorySerializer, PlaceListSerializer, PlaceDetailSerializer,
    ExpectationDefinitionSerializer, SortTagDefinitionSerializer,
    WheelSpinRequestSerializer, LikeRequestSerializer
)
from django.utils.translation import get_language, activate, override 

class ParlerViewSetMixin:
    pass

class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

class CategoryViewSet(ParlerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.prefetch_related('translations') # Optimise
    serializer_class = CategorySerializer

class PlaceViewSet(ParlerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = PlaceDetailSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PlaceFilter
    search_fields = ['translations__name', 'translations__description', 'address', 'category__translations__name']
    ordering_fields = ['translations__name', 'created_at', 'category__translations__name', 'popular']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PlaceListSerializer
        return PlaceDetailSerializer

    def get_queryset(self):
        queryset = Place.objects.language().filter(is_active=True).prefetch_related(
            'translations',
            'category__translations',
            'images',
            'open_times',
        )
        return queryset

    def retrieve(self, request, *args, **kwargs):
        current_lang_for_debug = get_language()
        instance = self.get_object()

        if current_lang_for_debug:
            instance.set_current_language(current_lang_for_debug)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], serializer_class=LikeRequestSerializer)
    def like(self, request, pk=None):
        place = self.get_object()
        serializer = LikeRequestSerializer(data=request.data)
        if serializer.is_valid():
            device_id = serializer.validated_data['device_id']
            is_liked_action = False
            if device_id in place.liked_by_devices:
                place.liked_by_devices.remove(device_id)
            else:
                place.liked_by_devices.append(device_id)
                is_liked_action = True
            place.save(update_fields=['liked_by_devices'])
            return Response({"success": True, "is_liked": is_liked_action, "like_count": len(place.liked_by_devices)}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseParlerAPIView(views.APIView):
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # context['lang_code'] = get_language() # Pass current language if needed by serializer explicitly
        context['request'] = self.request
        return context


class FilterOptionsView(BaseParlerAPIView):
    def get(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        regions = SortTagDefinition.objects.language().filter(type='region')
        expectations = ExpectationDefinition.objects.language().all()
        sort_tags = SortTagDefinition.objects.language().filter(type__in=['general', 'amenity'])
        place_types = Category.objects.language().all()

        return Response({
            "regions": SortTagDefinitionSerializer(regions, many=True, context=context).data,
            "expectations": ExpectationDefinitionSerializer(expectations, many=True, context=context).data,
            "sort_tags": SortTagDefinitionSerializer(sort_tags, many=True, context=context).data,
            "place_types": CategorySerializer(place_types, many=True, context=context).data,
        })

class WheelSpinView(BaseParlerAPIView):
    def post(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        request_serializer = WheelSpinRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = request_serializer.validated_data
        queryset = Place.objects.language().filter(is_active=True)

        if data.get('category_ids'):
            queryset = queryset.filter(category_id__in=data['category_ids'])

        for key in data.get('expectation_keys', []):
            field_mapping = { "outsideArea": "outside_area", "kardPay": "kard_pay", "coffee": "coffee", "meatAndChicken": "meat_and_chicken",
                             "insideArea": "inside_area", "reservation": "reservation", "kidsMenu": "kids_menu", "babySit": "baby_sit",
                            "cash": "cash", "freeParkArea": "free_park_area", "bar": "bar", "dessert": "dessert", "kitchen": "kitchen",
                            "WheelchairAccessibleEntrance": "wheelchair_accessible_entrance", "petsAllow": "pets_allow", "fish": "fish" }
            if key in field_mapping: queryset = queryset.filter(**{field_mapping[key]: True})
            elif hasattr(Place, key) and isinstance(Place._meta.get_field(key), models.BooleanField): queryset = queryset.filter(**{key: True})


        for key in data.get('region_keys', []):
            field_mapping = {"kyrenia": "kyrenia", "nicosia": "nicosia", "famagusta": "famagusta", "iskele": "iskele", "guzelyurt": "guzelyurt",
                             "karpaz": "karpaz", "lefke": "lefke" }
            if key in field_mapping: queryset = queryset.filter(**{field_mapping[key]: True})
            elif hasattr(Place, key) and isinstance(Place._meta.get_field(key), models.BooleanField): queryset = queryset.filter(**{key: True})


        if queryset.exists():
            count = queryset.count()
            if count > 0:
                random_index = random.randint(0, count - 1)
                place = queryset[random_index]
                return Response(PlaceDetailSerializer(place, context=context).data)

        return Response({"detail": ("No places found matching your criteria.")}, status=status.HTTP_404_NOT_FOUND)