# Generated by Django 5.1 on 2024-09-20 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flowers', '0012_order_total_price_alter_customuser_avatar_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='report',
            old_name='sale_data',
            new_name='total_sales',
        ),
        migrations.RemoveField(
            model_name='report',
            name='order',
        ),
        migrations.AddField(
            model_name='report',
            name='orders',
            field=models.TextField(default=''),
        ),
    ]
