# Generated manually for MemoirFormSubmission model - Fixed version

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scribble', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemoirFormSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(max_length=20)),
                ('gender', models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not_to_say', 'Prefer not to say')], max_length=20)),
                ('theme', models.CharField(help_text='Overall theme of the memoir', max_length=200)),
                ('subject', models.CharField(help_text='Subject of the memoir', max_length=200)),
                ('main_themes', models.TextField(help_text='Main themes to cover in the memoir')),
                ('key_life_events', models.TextField(help_text='Key life events to include')),
                ('audience', models.CharField(choices=[('family_friends', 'Family and Friends'), ('public', 'Public'), ('specific_group', 'Specific Group')], max_length=20)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('is_processed', models.BooleanField(default=False)),
                ('processing_notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Memoir Form Submission',
                'verbose_name_plural': 'Memoir Form Submissions',
                'ordering': ['-submitted_at'],
            },
        ),
    ] 