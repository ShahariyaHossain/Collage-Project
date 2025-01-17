# Generated by Django 5.1.3 on 2024-11-16 01:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fruitkha', '0014_alter_slider_background_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Final total for this cart item after discount', max_digits=10),
        ),
    ]
