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
from django.conf import settings

CLIENT_SECRETS_FILE = settings.CLIENT_SECRETS_FILE
SCOPES = ['https://www.googleapis.com/auth/youtube.upload' ,'https://www.googleapis.com/auth/gmail.send']

def send_email(creator,editor,id):

    emailMessage = MIMEMultipart('alternative')

    emailMessage["Subject"] = "Confirmation Email"

    emailMessage["From"] = "patelmilap89@gmail.com"

    emailMessage["To"] = creator.email

    email_text_part = MIMEText(f"Hey {creator.full_name},Hope you doi'n well. This is a Confirmation Email for a Video upload to your Youtube Channel from {editor.full_name}.","plain")

    emailMessage.attach(email_text_part)

    creds = Credentials(token=creator.credentials['token'])
    service = build('youtube','v3',credentials=creds)

    request = service.videos().list(part="snippet,contentDetails,statistics",id=id)

    video_details = request.execute()

    print(video_details)

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
                                <span style="font-weight:bold">Video Title</span> : 
                                </li>
                                
                                <li style="margin-top:20px;">
                                <span style="font-weight:bold">Video Description</span>  :
                                </li>

                                <li style="margin-top:20px;">
                                <span style="font-weight:bold">Video Tags</span>  : 
                                </li>

                                <li style="margin-top:20px;">
                                <span style="font-weight:bold">Video Privacy Status</span>  :
                                </li>
                                
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