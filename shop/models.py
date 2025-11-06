from django.db import models

# Create your models here.
from django.db import models

class Rating(models.Model):
    rate = models.FloatField()
    count = models.IntegerField()

    def __str__(self):
        return f"Rating: {self.rate} ({self.count} reviews)"

class Category(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='produto_imagens/')
    rating = models.OneToOneField(Rating, on_delete=models.CASCADE, related_name='produto')

    def __str__(self):
        return self.title
