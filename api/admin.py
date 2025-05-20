from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import (
    Language, Category, Place, PlaceImage, OpeningHour,
    ExpectationDefinition, SortTagDefinition
)

admin.site.register(Language)

@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    list_display = ('name', 'icon_key')

@admin.register(ExpectationDefinition)
class ExpectationDefinitionAdmin(TranslatableAdmin):
    list_display = ('key', 'name', 'icon_key')
    search_fields = ['key', 'translations__name', 'icon_key']


@admin.register(SortTagDefinition)
class SortTagDefinitionAdmin(TranslatableAdmin):
    list_display = ('key', 'name', 'type', 'icon_key')
    search_fields = ['key', 'translations__name', 'type', 'icon_key']


class PlaceImageInline(admin.TabularInline):
    model = PlaceImage
    extra = 1

class OpeningHourInline(admin.TabularInline):
    model = OpeningHour
    extra = 1

@admin.register(Place)
class PlaceAdmin(TranslatableAdmin):
    list_display = ('get_primary_name', 'get_category_name', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'kyrenia', 'nicosia')
    search_fields = ('translations__name', 'translations__description', 'address')
    inlines = [PlaceImageInline, OpeningHourInline]


    ordering = ('pk',)

    def get_primary_name(self, obj):
        return obj.safe_translation_getter('name', any_language=True)
    get_primary_name.short_description = 'Name'
    get_primary_name.admin_order_field = 'translations__name'

    def get_category_name(self, obj):
        if obj.category:
            return obj.category.safe_translation_getter('name', any_language=True)
        return None
    get_category_name.short_description = 'Category'
