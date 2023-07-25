#Abram Huang
#4/21/23
#Remote sensing
#Ring Doorbell

import numpy as np
import cv2
import imutils
import time
import pdb
import smtplib
from smtplib import SMTP
from smtplib import SMTPException
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime


# Video Recording Settings
cap=cv2.VideoCapture(0)
w=1280
h=720
cap.set(3,w)
cap.set(4,h)
fourcc=cv2.VideoWriter_fourcc(*'mp4v')


def mask_image (img):

    mask=np.zeros((img.shape[0],img.shape[1]),dtype="uint8")
    # forms mask for door shape
    pts=np.array([[391,116],[669,82],[678,1080],[378,1080]])
    cv2.fillConvexPoly(mask,pts,255)
    masked = cv2.bitwise_and(img,img,mask=mask)
    # applies mask and downsizes to processable image
    gray =imutils.resize(masked,width=300)
    # applies grayscale
    gray = cv2.cvtColor(gray,cv2.COLOR_BGR2GRAY)
    # Kernel Size of 11 was chosen as it worked with the smaller image width.
    # It also worked well in the uniform lighting conditions
    gray = cv2.GaussianBlur(gray,(11,11),0)
    return masked,gray



def compare_image(gray_1,gray_2):
    # Compare the two images
    # Pixel_threshold of 20 was used as it could detect if the door was creaked open
    pixel_threshold = 20

    detector_total = np.uint64(0)
    detector = np.zeros((gray_1.shape[0], gray_1.shape[1]), dtype="uint8")

    # pixel by pixel comparison
    for i in range(0, gray_1.shape[0]):
        for j in range(0, gray_1.shape[1]):
            if abs(int(gray_2[i, j])) - abs(int(gray_1[i, j])) > pixel_threshold:
                detector[i, j] = 255
    # sum the detector array
    detector_total = np.uint64(np.sum(detector))
    print("detector_total= ", detector_total)
    # Detector threshold was chosen through testing, how much the door had to be open to activate
    if detector_total >15000:
        print( "Intruder detected!")
        return True
    else:
        print("nothing detected")
    return False

# Recieves two images and emails them
def emailImages(time_stamp,img_one_str):
    # Email Settings
    time_stamp=time_stamp[0:len(time_stamp)-4]
    smtpUser = config.smtpUserKey
    smtpPass = config.smtpPassKey

    toAdd = smtpUser
    fromAdd = smtpUser
    subject = "Image recorded at " + time_stamp
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = fromAdd
    msg['To'] = toAdd
    msg.preamble = "Image recorded at " + time_stamp
    body = MIMEText("Image recorded at " + time_stamp)
    msg.attach(body)

    fp = open(img_one_str, 'rb')
    imgSent = MIMEImage(fp.read())
    fp.close()
    msg.attach(imgSent)

    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.ehlo()
    s.starttls()
    s.ehlo()

    s.login(smtpUser, smtpPass)
    s.sendmail(fromAdd, toAdd, msg.as_string())
    s.quit()
    print("email sent")


def main():
    camera=cv2.VideoCapture(0)
    timestr=""
    while camera.isOpened():
        ret,frame=camera.read()
        if ret == True:
            timeStart=time.time()
            img_one=frame
            maskFrame_1, gray_1 = mask_image(img_one)

            # Takes two images 30ms apart. time delay was started at 3ms (human percived motion limit) and gradually increaed
            while (time.time()-timeStart) <(30/1000):
                pass
            ret, frame = camera.read()
            img_two=frame
            maskFrame_2, gray_2 = mask_image(img_two)

            # compares masked image to see if pixel threshold is met
            if compare_image(gray_1,gray_2):
                # Records timestamp
                timestr = time.strftime("doorbell-%Y%m%d-%H%M%S.mp4")
                out = cv2.VideoWriter(timestr, fourcc, 20.0, (1280, 720))
                # initiates time to start recording
                timeVidStart = time.time()
                # Records a 21-23 second video while loop is running
                while ((time.time() - timeVidStart) < 15):
                    ret_a, frame_a = cap.read()
                    #Records frame into video
                    out.write(frame_a)
                img_one_str = "image_1.jpg"
                cv2.imwrite(img_one_str, img_one)
                # emails images to set email account
                emailImages(timestr, img_one_str)
            # Masked frame for demonstration purposes
            cv2.imshow("frame",maskFrame_1)

        if cv2.waitKey(25) & 0XFF == ord('q'):
            break
    camera.release()
    cap.release()
    out.release()
    cv2.destroyAllWindows()







if __name__=="__main__":
    main()