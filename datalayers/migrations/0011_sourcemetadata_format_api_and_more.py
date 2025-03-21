# Generated by Django 5.1.5 on 2025-02-12 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datalayers', '0010_alter_sourcemetadata_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcemetadata',
            name='format_api',
            field=models.BooleanField(default=False, help_text='Does this source use an API?'),
        ),
        migrations.AlterField(
            model_name='sourcemetadata',
            name='language',
            field=models.CharField(blank=True, help_text='Prefer ISO 639-3 language code, see <a target="_blank" href="https://iso639-3.sil.org/code_tables/639/data">SIL for full list</a>. Other ISO 639 codes are allowed as well.', max_length=255),
        ),
        migrations.AlterField(
            model_name='sourcemetadata',
            name='pid',
            field=models.CharField(blank=True, help_text='Fetching DOI data will overwrite name, license and DataCite fields.', max_length=255, verbose_name='PID'),
        ),
        migrations.AlterField(
            model_name='sourcemetadata',
            name='pid_type',
            field=models.CharField(blank=True, choices=[('URL', 'URL'), ('DOI', 'DOI'), ('ROR', 'ROR'), ('ORCID', 'ORCID')], default='', help_text='In case of URL put the URL into the PID field.', max_length=255, verbose_name='PID type'),
        ),
    ]
