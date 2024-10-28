from django.contrib import admin

from .models import Category, Genre, Title, Review, Comment, YamdbUser

admin.site.register(Category)
admin.site.register(Genre)
admin.site.register(Title)
admin.site.register(Review)
admin.site.register(Comment)


@admin.register(YamdbUser)
class YamdbUserAdmin(admin.ModelAdmin):
    list_display = ('confirmation_code',
                    'username',
                    'email',
                    'role',
                    'bio',
                    'pk')
    list_editable = ('role',)
    search_fields = ('username', 'role',)


admin.site.unregister(YamdbUser)
