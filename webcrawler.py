#Author: Salim Ali Siddiq
#Time: Jan 2016
#!/usr/bin/env python
import socket
from HTMLParser import HTMLParser
import sys
import re

#imported all neccessary packages

#inititalizing class
class Crawler(HTMLParser):

    #variables
    token = ''
    sessionID = ''
    datalist = []
    TraversedLink = []
    Counter = 0
    httpStatus = 0

    #Methods to parse HTML pages and fetch flags using HTMLParse
    #Crawler default constructor
    def __init__(self):
        #initializes variables of HMTLParser class
        HTMLParser.__init__(self)
        self.UrlFlag = False
        self.SecretFlag = False

    #method when HTML header is parsed
    def handle_starttag(self, tag, attribs):
        self.UrlFlag = False
        self.SecretFlag = False

        #URL inserted in datalist if not already traversed
        if tag == 'a':
            for name, value in attribs:
                if value not in Crawler.TraversedLink and value not in Crawler.datalist and value != None:
                    Crawler.datalist.append(value)

        #Check for secret_flag in present webpage
        if tag == 'h2':
            for name, value in attribs:
                if value == 'secret_flag' and name == 'class':
                    self.SecretFlag = True
                    break
                else:
                    return

    #Check for secret_flag in present webpage
    def handle_data(self, resp):
        #If secret_flag obtained, print it
        if self.SecretFlag == True:
            Crawler.Counter += 1
            print resp.split(': ')[1]


    #method to send the intial HTTP GET request
    def FirstGetMethod(self, url):
        try:
            #HTTP GET request header
            GETRequest = "GET " + str(url) + " HTTP/1.0\nConnection: keep-alive\n\n"

            #TCP socket initialization
            sock1 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            #Socket bind and connected to host at the port number
            sock1.connect(("cs5700sp16.ccs.neu.edu",80))

            #send GET request header through socket
            sock1.sendall(GETRequest)

            #receive response from the server through the socket
            response1 = sock1.recv(4096)

            #using  Regex module to fetch session ID and CSRF token
            session_pattern = re.compile(r'sessionid=([a-z0-9]+);')
            csrf_pattern = re.compile(r'csrftoken=([a-z0-9]+);')

            #HTTP status checked received in response
            self.checkStatus(response1,url)

            #feed() method is called to insert discovered links from the present page
            c1 = Crawler()
            c1.feed(response1)

            #make an HTTP POST request, when 200 OK status is received along with CSRF token
            if self.httpStatus == "200" and 'csrftoken' in response1:
                #CSRF token and SessionID
                self.token = csrf_pattern.findall(response1)[0]
                self.sessionID = session_pattern.findall(response1)[0]
                self.PostRequestMethod(url)

            #Close socket
            sock1.close()
        except:
            print ("Error!")
            sock1.close()

    # method for HTTP POST request to login to Fakebook
    def PostRequestMethod(self, presentUrl):
        try:
            #HTTP Post data
            postdata = "username="+self.username+"&password="+self.password+"&csrfmiddlewaretoken="+self.token + "&next=/fakebook/"

            #HTTP POST request header
            PostRequest = "POST " + presentUrl + " HTTP/1.0\r\nHost: cs5700sp16.ccs.neu.edu\r\nConnection: keep-alive\r\nContent-Length: 105 \
                  \r\nContent-Type: application/x-www-form-urlencoded\r\nCookie: csrftoken="+str(self.token) + "; sessionid=" + str(self.sessionID) + "\r\n\r\n" + postdata + "\n"

            #TCP socket initialization
            sock2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            #Socket bind and connected to host at the port number
            sock2.connect(("cs5700sp16.ccs.neu.edu",80))

            #send POST request header through socket
            sock2.sendall(PostRequest)

            #receive response from the server through the socket
            response2 = sock2.recv(4096)

            #using  Regex module to fetch session ID
            session_pattern = re.compile(r'sessionid=([a-z0-9]+);')

            #fetched SessionID
            self.sessionID = session_pattern.findall(response2)[0]

            #feed() method is called to insert discovered links from the present page
            cl = Crawler()
            cl.feed(response2)

            #Close socket
            sock2.close()

            # Crawl method called to traverse all URLs in the datalist
            self.crawl()
        except:
            print ("Error!")
            sock2.close()

    #method to send the HTTP GET request with cookies
    def GetMethod(self, url):
        try:
            #HTTP GET request header
            GETRequest1 = "GET " + str(url) + " HTTP/1.0\r\nHost: cs5700sp16.ccs.neu.edu\r\nCookie: csrftoken=" + str(self.token) + "; sessionid=" + str(self.sessionID) + "\r\n\r\n"

            #TCP socket initialization
            sock3 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            #Socket bind and connected to host at the port number
            sock3.connect(("cs5700sp16.ccs.neu.edu",80))

            #send GET request header through socket
            sock3.sendall(GETRequest1)

            #receive response from the server through the socket
            response3 = sock3.recv(4096)

            #HTTP status checked received in response
            self.checkStatus(response3,url)

            #feed() method is called to insert discovered links from the present page
            cl = Crawler()
            cl.feed(response3)

            #Close socket
            sock3.close()
        except:
            print ("Error!")
            sock3.close()


    #method to handle HTTP codes
    def checkStatus(self,resp,presentUrl):
        try:
            # get httpStatus code from response
            httpCode = resp.split(' ')[1]
            self.httpStatus = httpCode

            # if HTTP code 301 or 302 then Crawler fetches the new URL from the HTTP header
            if httpCode == "301" or httpCode == "302":
                self.httpStatus = httpCode
                newlink_pattern = re.compile(r'Location:[.\s]* .*')
                newLink = newlink_pattern.findall(resp)[0]
                redirectLink=newLink.split(' ')
                redirectedLink=redirectLink[1]
                #check whether or not user is logged in
                if self.sessionID == '':
                    self.FirstGetMethod(redirectedLink)
                else:
                    self.GetMethod(redirectedLink)

            #if HTTP code 500 then Crawler re-tries the request for the URL
            elif httpCode == "500":
                    self.httpStatus = httpCode
                    # check whether or not user is logged in
                    if self.sessionID == '':
                        self.FirstGetMethod(presentUrl)
                    else:
                        self.GetMethod(presentUrl)
        except:
            print ("Error!")


    #main method for the crawler
    def crawl(self):
        try:
            while len(self.datalist) > 0 and self.Counter  < 5:

                # datalist is a stack(LIFO)
                currentUrl = self.datalist[len(self.datalist) - 1]

                #Check if a url has not been traversed before
                if currentUrl not in self.TraversedLink:
                    #if not then GET the webpage and its urls
                    self.GetMethod(currentUrl)

                    #insert the current traversed url to the traversed list
                    self.TraversedLink.append(currentUrl)

                    #And remove current traversed url from datalist
                    self.datalist.remove(currentUrl)
                else:
                    #if yes, then remove the url from datalist
                    self.datalist.remove(currentUrl)
        except:
            print ("Error!")

    def startOfCode(self,usernameFromUser,pwdFromUser):
        self.username = usernameFromUser
        self.password = pwdFromUser
        self.FirstGetMethod("http://cs5700sp16.ccs.neu.edu/fakebook/")


#main try
try:
    #check number of arguments passed
    if len(sys.argv) == 3:
        #create object of class
        w=Crawler()
        #call function in class using object
        w.startOfCode(sys.argv[1],sys.argv[2])
    else:
        print ("Wrong input!")
except:
    print ("Error!")
