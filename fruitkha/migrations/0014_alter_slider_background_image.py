# Generated by Django 5.1.3 on 2024-11-15 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fruitkha', '0013_cartitem_coupon_product_slug_alter_cartitem_accounts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slider',
            name='background_image',
            field=models.ImageField(help_text='Background image for the slider', upload_to='slider_photos/'),
        ),
    ]
