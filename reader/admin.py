from django.contrib import admin
from .models import Document, Note, Bookmark, Highlight, ReadingProgress
admin.site.register(Document)
admin.site.register(Note)
admin.site.register(Bookmark)
admin.site.register(Highlight)
admin.site.register(ReadingProgress)
