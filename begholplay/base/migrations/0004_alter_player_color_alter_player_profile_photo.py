# Generated by Django 4.1 on 2024-08-15 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0003_alter_lobby_owner_alter_match_lobby_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="player",
            name="color",
            field=models.CharField(
                choices=[
                    ("#DC143C", "RED"),
                    ("#Ffa500", "ORANGE"),
                    ("#4169E1", "BLUE"),
                    ("#228B22", "GREEN"),
                    ("#DAA520", "GOLDEN-ROD"),
                    ("#708090", "GRAY"),
                    ("#EE82EE", "VIOLET"),
                    ("#F4A460", "BROWN"),
                    ("#00FFFF", "CYAN"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="player",
            name="profile_photo",
            field=models.ImageField(blank=True, null=True, upload_to="profile_photos/"),
        ),
    ]
