# Generated by Django 4.0.2 on 2022-04-18 01:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('c_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Warehouse',
            fields=[
                ('w_id', models.AutoField(primary_key=True, serialize=False)),
                ('loc_x', models.IntegerField()),
                ('loc_y', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('p_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='amazon.category')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('o_id', models.AutoField(primary_key=True, serialize=False)),
                ('loc_x', models.IntegerField()),
                ('loc_y', models.IntegerField()),
                ('ups_account', models.TextField(blank=True, default='')),
                ('card_number', models.DecimalField(decimal_places=0, max_digits=16)),
                ('status', models.CharField(choices=[('closed', 'closed'), ('open', 'open'), ('one_time', 'one_time')], default='open', max_length=10)),
                ('date', models.DateField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('i_id', models.AutoField(primary_key=True, serialize=False)),
                ('count', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('delivering', 'delivering'), ('new', 'new'), ('delivered', 'delivered'), ('packed', 'packed')], default='new', max_length=12)),
                ('ups_truckid', models.IntegerField(blank=True, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='amazon.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='amazon.product')),
            ],
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveIntegerField()),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='amazon.product')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='amazon.warehouse')),
            ],
            options={
                'unique_together': {('product', 'warehouse')},
            },
        ),
    ]
