# Generated by Django 5.1 on 2024-09-16 19:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flowers', '0004_cart_total_price_alter_cart_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='password1',
            field=models.CharField(default='password12345678', max_length=100),
        ),
        migrations.AddField(
            model_name='customuser',
            name='password2',
            field=models.CharField(default='password12345678', max_length=100),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='password',
            field=models.CharField(max_length=128, verbose_name='password'),
        ),
        migrations.CreateModel(
            name='EditProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, max_length=100, null=True)),
                ('email', models.EmailField(blank=True, max_length=100, null=True)),
                ('password', models.CharField(blank=True, max_length=100, null=True)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='media/avatars/')),
                ('first_name', models.CharField(blank=True, max_length=100, null=True)),
                ('last_name', models.CharField(blank=True, max_length=100, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]