# from django.db import models

# # Creating database
# # Create your models here.

# class Note(models.Model):
#     body = models.TextField()
#     updated = models.DateTimeField(auto_now=True)
#     created = models.DateTimeField(auto_now_add=True)
#     #thumb = models.ImageField()

#     def __str__(self):
#         return self.body[:50]
    
#     class Meta:
#         ordering = ['-updated']

from django.db import models
from django.utils import timezone

# Creating database
# Create your models here.

# class Note(models.Model):
#     # Field to store the name of the finger (e.g., "left_thumb", "right_four_fingers", etc.)
#     #finger_name = models.CharField(max_length=50)

#     # Fields to store the uploaded and processed images for each category
#     left_thumb = models.ImageField(upload_to='finger_images/left_thumb/', null=True, blank=True)
#     left_four_fingers = models.ImageField(upload_to='finger_images/left_four_fingers/', null=True, blank=True)
#     right_thumb = models.ImageField(upload_to='finger_images/right_thumb/', null=True, blank=True)
#     right_four_fingers = models.ImageField(upload_to='finger_images/right_four_fingers/', null=True, blank=True)

#     # Timestamps for record-keeping
#     updated = models.DateTimeField(auto_now=True)
#     created = models.DateTimeField(auto_now_add=True)

# class Note(models.Model):
#     image = models.ImageField(upload_to='uploads/', null=True, blank=True)
#     finger_name = models.CharField(max_length=100,null = True, blank = True)


#     def __str__(self):
#         return self.finger_name

#     # class Meta:
#     #     ordering = ['-updated']

# class ProcessedImage(models.Model):
#     original_image = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='processed_images')
#     processed_image = models.ImageField(upload_to='processed/',null = True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Processed Image {self.id}: {self.processed_image.name}"


from django.db import models

class Note(models.Model):
    FINGER_CHOICES = [
        ('left_thumb', 'Left Thumb'),
        ('left_four', 'Left Four Fingers'),
        ('right_thumb', 'Right Thumb'),
        ('right_four', 'Right Four Fingers'),
    ]
    
    image = models.ImageField(upload_to='uploads/', null=True, blank=True)
    finger_name = models.CharField(
        max_length=100,
        choices=FINGER_CHOICES,
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.finger_name} - {self.created_at}"

class ProcessedImage(models.Model):
    original_image = models.ForeignKey(
        Note, 
        on_delete=models.CASCADE, 
        related_name='processed_images',
        null=True,  # Add this
        blank=True
    )
    processed_image = models.ImageField(upload_to='processed/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Processed Image {self.id}: {self.processed_image.name}"

    class Meta:
        ordering = ['-created_at']
        
        