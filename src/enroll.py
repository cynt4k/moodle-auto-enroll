#!/usr/bin/env python
import getopt
import json
import sys
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import time
import smtplib
import socket
import email.utils
from email.message import EmailMessage
from threading import Thread


class Enroll(Thread):

    def __init__(self, configfile, username="", password="", delay=5):
        Thread.__init__(self)
        with open(configfile) as jsonData:
            self.config = json.load(jsonData)

        if username is not "":
            self.config["login"]["username"] = username
        if password is not "":
            self.config["login"]["password"] = password

        self.delay = delay
        self.mailserver = smtplib.SMTP()
        self.session = HTMLSession()
        self.msg = EmailMessage()

    def run(self):
        res = self.session.post(self.config["moodle"]["loginUrl"], data=self.config["login"])
        res_pretty = BeautifulSoup(res.text, "html.parser")

        failed = res_pretty.find("span", {"class": "error"})

        if failed:
            print("Invalid login data")
            sys.exit(1)

        self.msg = EmailMessage()
        self.msg["To"] = email.utils.formataddr(("Recipient", self.config["mail"]["to"]))
        self.msg["From"] = email.utils.formataddr(("Autoenroll Server", self.config["mail"]["from"]))
        self.msg["Subject"] = "Enrolled course"

        while True:
            self.checkchoice()

    def checkchoice(self):
        for course in self.config["moodle"]["courses"]:

            if course["finished"]:
                continue

            res = self.session.get(self.config["moodle"]["courseUrl"] + course["id"])
            res_pretty = BeautifulSoup(res.text, "html.parser")

            if res.status_code != 200:
                error = res_pretty.find("", {"class": "errormessage"}).next
                print(error)
                sys.exit(1)

            for choice in course["choices"]:

                if choice["choosen"]:
                    continue

                if not choice["primary"]:
                    primaryChoosen = False
                    for checkPrimary in course["choices"]:
                        if checkPrimary["choosen"] and checkPrimary["primary"]:
                            primaryChoosen = True
                            course["finished"] = True
                            break
                    if primaryChoosen:
                        continue

                data = {
                    "action": "makechoice",
                    "answer": res_pretty.find("input", {"id": choice["id"]}).attrs["value"],
                    "id": res_pretty.find("input", {"name": "id"}).attrs["value"],
                    "sesskey": res_pretty.find("input", {"name": "sesskey"}).attrs["value"]
                }

                res = self.session.post(self.config["moodle"]["choiceUrl"], data=data)

                if res.status_code == 404:
                    res_error = BeautifulSoup(res.text, "html.parser")
                    error = res_error.find("", {"class": "errormessage"}).next
                    print("Error for Course " + course["name"] + ": " + error)
                    time.sleep(self.delay)
                    continue
                else:
                    self.msg.set_content("Successfully enrolled to the course\n\n"
                                         "Name:\t" + course["name"] + "\n"
                                                                      "Choice:\t" + choice["name"])
                    choice["choosen"] = True
                    try:
                        self.mailserver = smtplib.SMTP(self.config["mail"]["server"])
                        self.mailserver.sendmail(from_addr=self.config["mail"]["from"],
                                                 to_addrs=self.config["mail"]["to"], msg=self.msg.as_string())
                    except socket.error as e:
                        print("Could not connect to Mailserver")
                        sys.exit(1)
                    except smtplib.SMTPException as e:
                        print(e)
                    finally:
                        self.mailserver.quit()
                        break


if __name__ == "__main__":
    username = ""
    password = ""
    delay = 5
    configs = []

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:p:d:c:")
    except getopt.GetoptError:
        print(sys.argv[0] + " -u <username> -p <password> -d <delay> -c \"<config1> <config2>\"")
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print(sys.argv[0] + " -u <username> -p <password> -d <delay> -c \"<config1> <config2>\"")
            sys.exit()
        elif opt == "-u":
            username = arg
        elif opt == "-p":
            password = arg
        elif opt == "-d":
            delay = int(arg)
        elif opt == "-c":
            configs = arg.split(" ")

    if len(configs) == 0:
        print("No config file provided")
        print(sys.argv[0] + " -u <username> -p <password> -d <delay> -c \"<config1> <config2>\"")
        sys.exit(1)

    # server1 = Enroll("config.json", username=username, password=password, delay=5).start()

    for config in configs:
        Enroll(config, username=username, password=password, delay=delay).start()

