from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('interview', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add voice_analytics to InterviewAnswer
        migrations.AddField(
            model_name='interviewanswer',
            name='voice_analytics',
            field=models.JSONField(default=dict),
        ),
        # Add session_type to InterviewSession
        migrations.AddField(
            model_name='interviewsession',
            name='session_type',
            field=models.CharField(
                choices=[('standard', 'Standard'), ('mock', 'Mock Interview')],
                default='standard',
                max_length=20,
            ),
        ),
        # Add recommended_topics to InterviewSession
        migrations.AddField(
            model_name='interviewsession',
            name='recommended_topics',
            field=models.JSONField(default=list),
        ),
        # Add BookmarkedQuestion model
        migrations.CreateModel(
            name='BookmarkedQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bookmarks',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bookmarks',
                    to='interview.interviewsession',
                )),
            ],
            options={'unique_together': {('user', 'session', 'question_text')}},
        ),
    ]
