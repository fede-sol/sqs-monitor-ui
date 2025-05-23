# Generated by Django 5.2 on 2025-05-04 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.CharField(max_length=255, unique=True)),
                ('queue_name', models.CharField(max_length=255)),
                ('topic_arn', models.CharField(blank=True, max_length=512, null=True)),
                ('body', models.TextField()),
                ('attributes', models.JSONField(blank=True, null=True)),
                ('state', models.CharField(default='RECEIVED', max_length=50)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
