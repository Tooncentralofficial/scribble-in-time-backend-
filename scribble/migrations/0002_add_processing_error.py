# Generated manually to add processing_error field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scribble', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='knowledgedocument',
            name='processing_error',
            field=models.TextField(blank=True, help_text='Error message if processing failed', null=True),
        ),
    ] 