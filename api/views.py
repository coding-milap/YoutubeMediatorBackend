from django.shortcuts import render,reverse,redirect
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes,authentication_classes,parser_classes
from rest_framework.permissions import AllowAny,IsAuthenticatedOrReadOnly,IsAuthenticated
from .models import CustomUser,CreatorToEditorLink,Video
from .serializers import UserRegisterSerializer,IndexPageSerializer,UserProfileSerializer,NotificationsSerializer
from rest_framework import status
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser,FormParser,FileUploadParser
import cloudinary
from django.conf import settings
from rest_framework.views import APIView
from .serializers import VideoUploadSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Video
import os
import requests
from google.oauth2.credentials import Credentials
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient import errors
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
import threading
import random
import time
import httplib2




CLIENT_SECRETS_FILE = settings.CLIENT_SECRETS_FILE
SCOPES = ['https://www.googleapis.com/auth/youtube.upload' ,'https://www.googleapis.com/auth/gmail.send']

@api_view(['POST'])
@permission_classes([AllowAny])
def user_register(request):
    
    if request.method == "POST":

        user_serializer = UserRegisterSerializer(data=request.data)

        if user_serializer.is_valid():

            user_serializer.save()

            return Response(user_serializer.data,status=status.HTTP_201_CREATED)
    
        return Response(user_serializer.errors,status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])   
@permission_classes([IsAuthenticated])
def index(request):

    paginator = PageNumberPagination()
    paginator.page_size = 6
    
    user = CustomUser.objects.filter(email=request.user).first()

    if user.type == "CREATOR":

        editors = CustomUser.objects.filter(type="EDITOR")
      
        connected_editors = CreatorToEditorLink.objects.filter(Q(status="PENDING") | Q(status="CONNECTED")).filter(creator=user).values_list('editor_id',flat=True).distinct()

        remaining_editors = editors.exclude(id__in=connected_editors)
        
        remaining_editors = paginator.paginate_queryset(remaining_editors,request)

        editors_serializers = IndexPageSerializer(remaining_editors,many=True)

        return paginator.get_paginated_response(editors_serializers.data)
    
    if user.type == "EDITOR":

        creators = CustomUser.objects.filter(type="CREATOR")

        connected_creators = CreatorToEditorLink.objects.filter(Q(status="PENDING") | Q(status="CONNECTED")).filter(editor=user).values_list('creator_id',flat=True).distinct()

        remaining_creators = creators.exclude(id__in=connected_creators)

        remaining_creators = paginator.paginate_queryset(remaining_creators,request)

        creators_serializers = IndexPageSerializer(remaining_creators,many=True)

        return paginator.get_paginated_response(creators_serializers.data)


    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])   
@permission_classes([IsAuthenticated])
def notifications(request):

    user = CustomUser.objects.filter(email=request.user).first()

    if user.type == "CREATOR":

        connection_requests = CreatorToEditorLink.objects.filter(creator=user).filter(status="PENDING").filter(created_by="EDITOR")

        editors = []

        for conn in connection_requests:

            editors.append(conn.editor)

        pending_editors = IndexPageSerializer(editors,many=True)

        return Response(pending_editors.data,status=status.HTTP_200_OK)
    
    else:

        connection_requests = CreatorToEditorLink.objects.filter(editor=user).filter(status="PENDING").filter(created_by="CREATOR")

        creators = []

        for conn in connection_requests:

            creators.append(conn.creator)

        pending_creators = IndexPageSerializer(creators,many=True)

        return Response(pending_creators.data,status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def send_connection_request(request,user_email):

    user = CustomUser.objects.filter(email=request.user).first()

    if user.type == "CREATOR":

        editor = CustomUser.objects.filter(email=user_email).first()

        link = CreatorToEditorLink.objects.create(creator=user,editor=editor,status="PENDING",created_by="CREATOR")

        link.save()

        return Response({"msg": "Request has been sent successfully"})

    else:

        creator = CustomUser.objects.filter(email=user_email).first()

        link = CreatorToEditorLink.objects.create(creator=creator,editor=user,status="PENDING",created_by="EDITOR")

        link.save()

        return Response({"msg": "Request has been sent successfully"})
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def accept_connection_request(request,user_email):

    user = CustomUser.objects.filter(email=request.user).first()

    if user.type == "CREATOR":
        
        editor = CustomUser.objects.filter(email=user_email).first()

        link = CreatorToEditorLink.objects.filter(creator=user).filter(editor=editor).first()

        link.status = "CONNECTED"

        link.save()

        return Response({"msg":"Accepted"})
    
    else:

        creator = CustomUser.objects.filter(email=user_email).first()

        link = CreatorToEditorLink.objects.filter(creator=creator).filter(editor=user).first()

        link.status = "CONNECTED"

        link.save()

        return Response({"msg": "Accepted"})

@api_view(["GET","PUT"])   
@permission_classes([IsAuthenticated])
def user_profile(request):

    if request.method == "GET":
        try:
            user = CustomUser.objects.filter(email=request.user).first()

            user_serializer = UserProfileSerializer(user)

            return Response(user_serializer.data,status=status.HTTP_200_OK)
        except:

            return Response({'msg':'No user found'},status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == "PUT":

        user = CustomUser.objects.filter(email=request.user).first()

        user_serializer = UserProfileSerializer(user,data=request.data)

        if user_serializer.is_valid():

            user_serializer.save()

            return Response(user_serializer.data,status=status.HTTP_201_CREATED)
        
        return Response(user_serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cancel_request(request,user_email):

    user = CustomUser.objects.filter(email=request.user).first()

    if user.type == "CREATOR":
        editor = CustomUser.objects.filter(email=user_email).first()
        link = CreatorToEditorLink.objects.filter(creator=user,editor=editor,status="PENDING").first()

        if link :
            link.delete()

            return Response({'msg':'Request have been cancelled'},status=status.HTTP_200_OK)
    else:

        creator = CustomUser.objects.filter(email=user_email).first()
        link = CreatorToEditorLink.objects.filter(creator=creator,editor=user,status="PENDING")

        if link:

            link.delete()

            return Response({'msg':'Request have been cancelled'},status=status.HTTP_200_OK)


class VideoView(APIView):

    parser_classes = (MultiPartParser,FormParser)

    def post(self,request,*args,**kwargs):

        serializer = VideoUploadSerializer(data=request.data)

        if serializer.is_valid():

            video = serializer.save()
      
            try:
            
                video = Video.objects.filter(id=video.id).first()

                # response = cloudinary_upload(video,request.FILES['video_file'])

                # if not response:
                        
                #         base_dir = settings.BASE_DIR

                #         relative_path = os.path.join('media',video.video_file.name)

                #         video_file = os.path.join(base_dir,relative_path)

                #         video.delete()

                #         os.remove(video_file)
                        
                #         return Response({'msg':"Video is not Uploaded."})

                creator = video.user
                editor = request.user
                # video_url = video.cloudinary_id
                video_url = video.video_file
                video = video
                print('1')
                    
                try:
                    res = send_email(creator,editor,video_url,video)

                    if res:

                        return Response(serializer.data,status=status.HTTP_200_OK)

                except:

                    base_dir = settings.BASE_DIR

                    relative_path = os.path.join('media',video.video_file.name)

                    video_file = os.path.join(base_dir,relative_path)

                    print(video_file)

                    video.delete()

                    os.remove(video_file)

                    return Response({'msg':"Video is not Uploaded."},status=status.HTTP_400_BAD_REQUEST)

            except:
                pass
    
        return Response(serializer.errors)


def cloudinary_upload(video,video_file):

    try:

        result = cloudinary.uploader.upload_large(video_file,upload_preset=settings.CLOUDINARY_PRESET,resource_type = "video",chunk_size = 6000000)
    except:

        return False

    if result:

        video.cloudinary_id = result['url']

        video.save()

        return True

    return False


def send_email(creator,editor,video_url,video):

    emailMessage = MIMEMultipart('alternative')

    emailMessage["Subject"] = "Confirmation Email"

    emailMessage["From"] = "patelmilap89@gmail.com"

    emailMessage["To"] = creator.email

    email_text_part = MIMEText(f"Hey {creator.full_name},Hope you doi'n well. This is a Confirmation Email for a Video upload to your Youtube Channel from {editor.full_name}.","plain")

    emailMessage.attach(email_text_part)

    email_html_part = MIMEText(f"""

        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>YoutubeMediator - Confirmation Email</title>
            </head>
            <body>
    
                <div style=" background-color:#111827; color:white; font-family:'Verdana';padding:20px; max-widht:600px; margin:0 auto ">
                        <h1 style="text-align:center;">
                            Youtube Mediator
                        </h1>
                
                        <div>
                            <h3>
                            Hello Milap,
                            </h3>
                            
                            <p>
                                Hey {creator.full_name}, Hope you doing well. This is a Confirmation Email for a Video upload to your Youtube Channel which was intiated by {editor.full_name}. If you think this is not a valid request then you can cancel it by clicking cancel button.
                            </p>
                            
                            <h2 style="text-align:center"> Details of the Video </h2>
                            
                            <p>
                            <ol style="list-style-type:none">
                                
                                <li style="margin-top:30px;">
                                <span style="font-weight:bold">Video Title</span> : {video.title}
                                </li>
                                
                                <li style="margin-top:20px;">
                                <span style="font-weight:bold">Video Description</span>  : {video.description}
                                </li>

                                <li style="margin-top:20px;">
                                <span style="font-weight:bold">Video Tags</span>  : {video.tags}
                                </li>

                                <li style="margin-top:20px;">
                                <span style="font-weight:bold">Video Privacy Status</span>  : {video.privacy_status}
                                </li>
                                
                                # <li style="margin-top:20px;">
                                # <span style="font-weight:bold">Video URL</span>  : <a id="video-link" href=https://youtubemediatorbackend.onrender.com/{video_url} style="text-decoration:none; color: #3949AB;" >Video Link</a>
                                # </li>

                                <div style="margin-top:20px;">
                                    <a href={settings.REDIRECT_URI}/confirmation-page style="background-color: #04AA6D;
                                    border: none;
                                    font-size: 18px;
                                    color: #000000;
                                    padding: 10px;
                                    width: 100px;
                                    border-radius:4px;
                                    text-decoration:none;
                                    text-align: center;"> <span>Accept</span>
                                    </a> 
                                </div>
                                
                            </ol>
                            </p>
                        </div>
                    
                   </div>
  
            </body>
        </html>
    ""","html")

    emailMessage.attach(email_html_part)

    try:
        creds = Credentials(token=creator.credentials['token'])
        service = build('gmail','v1',credentials=creds)
        raw_email_message = base64.urlsafe_b64encode(emailMessage.as_bytes()).decode()

        service.users().messages().send(userId="me",body={"raw":raw_email_message}).execute()
        
        print("Email Sent Successfully")

        return True

    except RefreshError as err:
        
        token_url = settings.TOKEN_URL

        headers = {
            "Content-Type" : "application/x-www-form-urlencoded"
        }

        data= {
            "client_id" : settings.CLIENT_ID,
            "client_secret" : settings.CLIENT_SECRET,
            "refresh_token" : creator.credentials['refresh_token'],
            "grant_type" : "refresh_token"
        }

        response = requests.post(token_url,headers=headers,data=data)

        creator.credentials['token'] = response.json()['access_token']

        creator.save()

        creds = Credentials(token=creator.credentials['token'])
        service = build('gmail','v1',credentials=creds)
        raw_email_message = base64.urlsafe_b64encode(emailMessage.as_bytes()).decode()

        service.users().messages().send(userId="me",body={"raw":raw_email_message}).execute()
        
        return True

    except errors as error:
        print(error)
        return False


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def connected_users(request):

    user = CustomUser.objects.filter(email=request.user).first()

    creators_list = CreatorToEditorLink.objects.filter(editor=user).filter(status="CONNECTED")

    creators = []

    for creator in creators_list:

        creators.append(creator.creator)

    
    creator_serializer = IndexPageSerializer(creators,many=True)

    return Response(creator_serializer.data,status=status.HTTP_200_OK)


def authorize(request,user):

    if not user:

        return redirect(settings.REDIRECT_URI)

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = request.build_absolute_uri(reverse('oauth2callback'))

    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')

    request.session['state'] = state

    request.session['user'] = user

    return redirect(authorization_url)


def oauth2callback(request):
    print(request.session['user'])
    
    state = request.session['state']

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = request.build_absolute_uri(reverse('oauth2callback'))

    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    credentials_dict = credentials_to_dict(credentials)
    print(request.session['user'])
    user = request.session['user']
    creator = CustomUser.objects.filter(email=user).first()
    creator.credentials=credentials_dict
    creator.save()

    # print(creator.credentials)
    
    return redirect(settings.REDIRECT_URI)


def credentials_to_dict(credentials):
    return {'token': credentials.token, 'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri, 'client_id': credentials.client_id,
            'client_secret': credentials.client_secret, 'scopes': credentials.scopes}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def video_details(request):

    creator = request.user
    

    if creator:

        try:
            video = Video.objects.filter(user=creator).order_by('-created_at').first()
          
            serializer = VideoUploadSerializer(video)

            return Response(serializer.data)
        
        except:

            return Response({'msg':'No data'})
    else:

        return Response({'msg':"No data"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])  
def cancel_upload(request):

    try:

        user = CustomUser.objects.filter(email=request.user).first()

        base_dir = settings.BASE_DIR

        video = Video.objects.filter(user=user).first()

        relative_path = os.path.join('media',video.video_file.name)

        video_file = os.path.join(base_dir,relative_path)

        video.delete()

        os.remove(video_file)

        return Response({'msg':'Video Deleted Successfully'})
    except:

        return Response({'msg': 'Something went wrong.'})




httplib2.RETRIES = 1

MAX_RETRIES = 10

RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError,)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def upload_to_youtube(request):

    user = request.user

    youtube_upload_thread = threading.Thread(target=youtube_upload_2,args=(user,))

    youtube_upload_thread.start()

    return Response({'msg':'Upload Started'})


def youtube_upload_2(user):
    print('1')

    creator = CustomUser.objects.filter(email=user).first()
    creds = Credentials(token=creator.credentials['token'])
    service = build('youtube','v3',credentials=creds)
    print('2')

    video = Video.objects.filter(user=creator).first()

    if not video:
        print("hello")
        return

    base_dir = settings.BASE_DIR

    relative_path = os.path.join('media',video.video_file.name)

    video_file = os.path.join(base_dir,relative_path)

    body=dict(
    snippet=dict(
      title=video.title,
      description=video.description,
      tags=video.tags,
    ),
    status=dict(
      privacyStatus=video.privacy_status
    )
  )
    
    try:

        insert_request = service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
    )

        response = None
        error = None
        retry = 0

        while response is None:

            try:
                status,response = insert_request.next_chunk()

                if response is not None:

                    if 'id' in response:

                        print("Video was successfully uploaded." , response['id'])
                        video.delete()
                        os.remove(video_file)
                        Response({'msg':'SUCCESS'})
            except RETRIABLE_EXCEPTIONS as e:

                retry = retry + 1

                if retry > MAX_RETRIES:
                    
                    video.delete()

                    os.remove(video_file)

                    return Response({'msg':'not uploaded to youtube'})
                max_sleep = 2 ** retry

                sleep_seconds = random.random() * max_sleep

                time.sleep(sleep_seconds)
    except RefreshError as err :

        token_url = settings.TOKEN_URL

        headers = {
            "Content-Type" : "application/x-www-form-urlencoded"
        }

        data= {
            "client_id" : settings.CLIENT_ID,
            "client_secret" : settings.CLIENT_SECRET,
            "refresh_token" : creator.credentials['refresh_token'],
            "grant_type" : "refresh_token"
        }

        response = requests.post(token_url,headers=headers,data=data)

        creator.credentials['token'] = response.json()['access_token']

        creator.save()

        insert_request = service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
        )

        response = None
        error = None
        retry = 0

        while response is None:

            try:
                status,response = insert_request.next_chunk()

                if response is not None:

                    if 'id' in response:

                        print("Video was successfully uploaded." , response['id'])
                        video.delete()
                        os.remove(video_file)
                        Response({'msg':'SUCCESS'})
            except RETRIABLE_EXCEPTIONS as e:

                retry = retry + 1

                if retry > MAX_RETRIES:
                    
                    video.delete()

                    os.remove(video_file)

                    return Response({'msg':'not uploaded to youtube'})
                max_sleep = 2 ** retry

                sleep_seconds = random.random() * max_sleep

                time.sleep(sleep_seconds)
    except:
        video.delete()
        os.remove(video_file)
        return Response({'msg':"Not uploaded"})
        



