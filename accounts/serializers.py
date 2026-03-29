from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # hide password in response
    
    class Meta:
        model = User
        fields = ['username', 'password', 'cf_handle']  # fields for API
        
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)  
        # create_user hashes password automatically