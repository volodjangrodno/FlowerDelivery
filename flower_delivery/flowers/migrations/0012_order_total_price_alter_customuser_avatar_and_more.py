# Generated by Django 5.1 on 2024-09-18 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flowers', '0011_orderitem_amount_orderitem_total_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='avatar',
            field=models.ImageField(blank=True, default='media/catalog/default_user.png', upload_to='flowers/static/flowers/img/catalog/'),
        ),
        migrations.AlterField(
            model_name='editprofile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='flowers/static/flowers/img/catalog/'),
        ),
    ]
