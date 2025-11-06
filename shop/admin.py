from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Rating)
admin.site.register(Category)
admin.site.register(Product)