from django.db import models
from django.conf import settings


class QuestionBank(models.Model):
    CATEGORY_CHOICES = [
        ('python',        'Python'),
        ('django',        'Django'),
        ('dsa',           'Data Structures & Algorithms'),
        ('system_design', 'System Design'),
        ('behavioral',    'Behavioral'),
        ('javascript',    'JavaScript'),
        ('database',      'Database / SQL'),
        ('devops',        'DevOps'),
        ('ml',            'Machine Learning'),
    ]
    DIFFICULTY_CHOICES = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]

    category              = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    difficulty            = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    question_text         = models.TextField()
    expected_keywords     = models.JSONField(default=list)
    ideal_answer_outline  = models.TextField(blank=True)
    time_limit_seconds    = models.IntegerField(default=120)
    created_at            = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'[{self.category}] {self.question_text[:70]}'


class InterviewSession(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    SESSION_TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('mock',     'Mock Interview'),
    ]

    user             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions')
    title            = models.CharField(max_length=200, blank=True)
    category         = models.CharField(max_length=30, default='python')
    difficulty       = models.CharField(max_length=10, default='medium')
    session_type     = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='standard')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_questions  = models.IntegerField(default=5)
    overall_score    = models.FloatField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    sentiment_score  = models.FloatField(null=True, blank=True)
    feedback_summary = models.TextField(blank=True)
    improvement_tips = models.JSONField(default=list)
    strengths        = models.JSONField(default=list)
    recommended_topics = models.JSONField(default=list)
    readiness        = models.CharField(max_length=30, blank=True)
    started_at       = models.DateTimeField(null=True, blank=True)
    ended_at         = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} | {self.category} | {self.status}'

    @property
    def duration_minutes(self):
        if self.started_at and self.ended_at:
            return round((self.ended_at - self.started_at).seconds / 60, 1)
        return None

    @property
    def score_color(self):
        if self.overall_score is None:
            return 'gray'
        if self.overall_score >= 7:
            return 'green'
        if self.overall_score >= 5:
            return 'yellow'
        return 'red'


class InterviewAnswer(models.Model):
    session               = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='answers')
    # question FK is optional — AI-generated questions don't live in QuestionBank
    question              = models.ForeignKey(QuestionBank, on_delete=models.SET_NULL, null=True, blank=True)
    question_text         = models.TextField()
    answer_text           = models.TextField(blank=True)
    audio_file            = models.FileField(upload_to='audio/', null=True, blank=True)
    transcribed_text      = models.TextField(blank=True)
    score                 = models.FloatField(null=True, blank=True)
    confidence_score      = models.FloatField(null=True, blank=True)
    sentiment             = models.CharField(max_length=20, blank=True)
    sentiment_score       = models.FloatField(null=True, blank=True)
    keywords_matched      = models.JSONField(default=list)
    ai_feedback           = models.TextField(blank=True)
    improvement_suggestions = models.TextField(blank=True)
    face_emotions         = models.JSONField(default=dict)
    voice_analytics       = models.JSONField(default=dict)
    time_taken_seconds    = models.IntegerField(default=0)
    answered_at           = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Answer #{self.pk} | Session {self.session_id}'

    @property
    def score_pct(self):
        return int((self.score or 0) * 10)


class FacialSnapshot(models.Model):
    answer           = models.ForeignKey(InterviewAnswer, on_delete=models.CASCADE, related_name='snapshots')
    image            = models.ImageField(upload_to='snapshots/')
    dominant_emotion = models.CharField(max_length=30, blank=True)
    emotions_data    = models.JSONField(default=dict)
    captured_at      = models.DateTimeField(auto_now_add=True)


class BookmarkedQuestion(models.Model):
    """Feature 7: Bookmark questions for focused re-practice."""
    user          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    session       = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='bookmarks')
    question_text = models.TextField()
    note          = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'session', 'question_text')

    def __str__(self):
        return f'{self.user.email} | {self.question_text[:60]}'
