from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('interview', '0003_new_features'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interviewanswer',
            name='question',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='interview.questionbank',
            ),
        ),
    ]
