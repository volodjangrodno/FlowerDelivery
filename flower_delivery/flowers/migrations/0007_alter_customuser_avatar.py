# Generated by Django 5.1 on 2024-09-17 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flowers', '0006_remove_customuser_password1_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='avatar',
            field=models.ImageField(blank=True, default='media/catalog/default_user.png', upload_to='media/catalog/'),
        ),
    ]
