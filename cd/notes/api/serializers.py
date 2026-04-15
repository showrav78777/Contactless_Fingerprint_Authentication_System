# from rest_framework.serializers import ModelSerializer
# from .models import Note
# from .models import ProcessedImage

# class NoteSerializer(ModelSerializer):
#     class Meta:
#         model = Note
#         fields = '__all__'

# class ProcessedImageSerializer(ModelSerializer):
#     class Meta:
#         model = ProcessedImage
#         fields = '__all__'


from rest_framework import serializers
from .models import Note, ProcessedImage

class ProcessedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedImage
        fields = ['id', 'processed_image', 'created_at']
        read_only_fields = ['created_at']

class NoteSerializer(serializers.ModelSerializer):
    processed_images = ProcessedImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Note
        fields = ['id', 'image', 'finger_name', 'created_at', 'updated_at', 'processed_images']
        read_only_fields = ['created_at', 'updated_at']

    def validate_finger_name(self, value):
        valid_names = ['left_thumb', 'left_four', 'right_thumb', 'right_four']
        if value and value not in valid_names:
            raise serializers.ValidationError(f"Invalid finger name. Must be one of: {', '.join(valid_names)}")
        return value