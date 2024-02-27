from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import CustomUser,CreatorToEditorLink,Video


class UserRegisterSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(required=True,validators=[UniqueValidator(queryset=CustomUser.objects.all())])

    class Meta:

        model = CustomUser
        fields = ['email','full_name','type','password']

    
    def create(self,validated_data):

        user = CustomUser.objects.create(
            email = validated_data["email"],
            full_name = validated_data["full_name"],
            type = validated_data["type"],
        )

        user.set_password(validated_data["password"])

        user.save()

        return user

class IndexPageSerializer(serializers.ModelSerializer):

    class Meta:

        model = CustomUser
        fields = ['id','email','full_name',"type",'avatar']

class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:

        model = CustomUser
        fields = ['id','email','full_name','type','avatar','credentials']
    

    def update(self, instance, validated_data):

        instance.email = validated_data.get('email',instance.email)
        instance.full_name = validated_data.get('full_name',instance.full_name)
        instance.avatar = validated_data.get('avatar',instance.avatar)
        instance.credentials = validated_data.get('credentials',instance.credentials)

        instance.save()

        return instance


class NotificationsSerializer(serializers.ModelSerializer):

    class Meta:

        model = CreatorToEditorLink
        fields = ['creator','editor','status','created_by']


class VideoUploadSerializer(serializers.ModelSerializer):

    class Meta:

        model = Video
        fields = ['user','title','description','tags','privacy_status','video_file','cloudinary_id']


    


