# Generated initial migration
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Document", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("title",models.CharField(max_length=240)),
            ("pdf",models.FileField(upload_to="documents/%Y/%m/",validators=[django.core.validators.FileExtensionValidator(["pdf"])])),
            ("original_name",models.CharField(max_length=255)),
            ("uploaded_at",models.DateTimeField(auto_now_add=True)),
            ("last_page",models.PositiveIntegerField(default=1)),
            ("last_zoom",models.FloatField(default=1.0)),
            ("owner",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="documents",to=settings.AUTH_USER_MODEL)),
        ],options={"ordering":["-uploaded_at"]}),
        migrations.CreateModel(name="Bookmark", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("page",models.PositiveIntegerField(default=1)),("label",models.CharField(blank=True,max_length=200)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("document",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="bookmarks",to="reader.document")),
            ("owner",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="reader_bookmarks",to=settings.AUTH_USER_MODEL)),
        ],options={"ordering":["page","created_at"]}),
        migrations.CreateModel(name="Highlight", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("text",models.TextField()),("page",models.PositiveIntegerField(default=1)),("color",models.CharField(default="yellow",max_length=20)),("created_at",models.DateTimeField(auto_now_add=True)),
            ("document",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="highlights",to="reader.document")),
            ("owner",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="reader_highlights",to=settings.AUTH_USER_MODEL)),
        ],options={"ordering":["-created_at"]}),
        migrations.CreateModel(name="Note", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("text",models.TextField()),("page",models.PositiveIntegerField(default=1)),("created_at",models.DateTimeField(auto_now_add=True)),
            ("document",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="notes",to="reader.document")),
            ("owner",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="reader_notes",to=settings.AUTH_USER_MODEL)),
        ],options={"ordering":["-created_at"]}),
        migrations.CreateModel(name="ReadingProgress", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("page",models.PositiveIntegerField(default=1)),("updated_at",models.DateTimeField(auto_now=True)),
            ("document",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="progress",to="reader.document")),
            ("owner",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="reading_progress",to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.AddConstraint(model_name="bookmark",constraint=models.UniqueConstraint(fields=("owner","document","page"),name="unique_user_doc_bookmark_page")),
    ]
