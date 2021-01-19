import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

import os


def send_mail(text='Email Body', subject='Hello World', from_email='', to_emails=None, host=None, user_mailserver='',
              pw_mailserver='', html_file_path=None, html=None, html_inserts=None, image_file_paths=None,
              att_file_paths=None):
    assert to_emails is not None, "to_emails cannot be None."
    assert isinstance(to_emails, list), "To emails is not a list."
    assert host is not None, "Host cannot be None."
    assert len(from_email) > 0, 'From email cannot be empty'


    # EMAIL OBJECT
    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = ",".join(to_emails)
    msg['Subject'] = subject

    txt_part = MIMEText(text, 'plain')
    msg.attach(txt_part)

    # attach html
    if html_file_path is not None:
        if os.path.isfile(html_file_path):
            with open(html_file_path, 'r') as f:
                html = f.read()

            if html_inserts is not None:
                text_parts = html.split("</style>")
                part_1 = text_parts[0]
                part_2 = text_parts[1].format(**html_inserts)
                html = part_1 + "\n \t</style> \n" + part_2

            html_part = MIMEText(html, 'html')
            msg.attach(html_part)
        else:
            raise Exception("html_file_path is incorrect.")
    elif html is not None:

            if html_inserts is not None:
                if not isinstance(html_inserts, dict):
                    raise Exception("html_inserts is not a dictionary")

                text_parts = html.split("</style>")
                part_1 = text_parts[0]
                part_2 = text_parts[1].format(**html_inserts)
                html = part_1 + "</style>" + part_2

            html_part = MIMEText(html, 'html')
            msg.attach(html_part)

    # attach images - embedded
    if html_inserts is not None:
        if isinstance(html_inserts, dict):

            keys_str = " ".join(list(html_inserts.keys()))
            keys = list(html_inserts.keys())
            if 'cid' in keys_str:
                for key in keys:
                    if 'cid' in key:
                        cid = html_inserts[key]
                        path = html_inserts[key]
                        if os.path.isfile(path):
                            with open(path, 'rb') as f:
                                image = f.read()
                                image_name = f.name

                            image_part = MIMEImage(image, name=image_name)
                            image_part.add_header('Content-ID', f"<{cid}>")
                            msg.attach(image_part)
                        else:
                            raise Exception(f"{path} is not a correct file path.")
        else:
            raise Exception("html_inserts has to be a dictionary.")

    # attach image - not embedded
    if image_file_paths is not None:
        if isinstance(image_file_paths, list):
            for path in image_file_paths:
                if os.path.isfile(path):
                    with open(path, 'rb') as f:
                        image = f.read()
                        image_name = f.name
                        try:
                            image_name = image_name.split("/")[-1]
                        except:
                            pass
                    image_part = MIMEImage(image, name=image_name)
                    msg.attach(image_part)
                else:
                    raise Exception(f"{path} is not a correct file path.")
        elif isinstance(image_file_paths, str):
            if os.path.isfile(image_file_paths):
                with open(image_file_paths, 'rb') as f:
                    image = f.read()
                    image_name = f.name
                    try:
                        image_name = image_name.split("/")[-1]
                    except:
                        pass
                image_part = MIMEImage(image, name=image_name)
                msg.attach(image_part)
        else:
            raise Exception("image_file_paths is not of the correct format. Must be a string or list.")

    # attach files
    if att_file_paths is not None:
        if isinstance(att_file_paths, list):
            for path in att_file_paths:
                if os.path.isfile(path):
                    with open(path, 'rb') as f:
                        file = f.read()
                        file_name = f.name
                        try:
                            file_name = file_name.split("/")[-1]
                        except:
                            pass
                    file_part = MIMEApplication(file, name=file_name)
                    msg.attach(file_part)
                else:
                    raise Exception(f"{path} is not a correct file path.")
        elif isinstance(att_file_paths, str):
            if os.path.isfile(att_file_paths):
                with open(att_file_paths, 'rb') as f:
                    file = f.read()
                    file_name = f.name
                    try:
                        file_name = file_name.split("/")[-1]
                    except:
                        pass
                file_part = MIMEApplication(file, name=file_name)
                msg.attach(file_part)
        else:
            raise Exception("att_file_paths is not of the correct format. Must be a string or list.")

    msg_str = msg.as_string()

    # SEND EMAIL
    # login to my smtp server:
    # 1 create server, 2 configure(ehlo), 3 secure(starttls), 4 login
    server = smtplib.SMTP(host=host, port=587)
    server.ehlo()  # identifies with server
    server.starttls()  # creates a secure connection
    server.ehlo()  # identifies with server as encrypted connection

    server.login(user_mailserver, pw_mailserver)  # login
    server.sendmail(from_email, to_emails, msg_str)
    server.quit()
