import random
import socketserver
import threading
import time

HOST = '192.168.31.87'
PORT = 9900
lock = threading.Lock()

userlist = ["김중규", "정재현", "허민재", "이윤서", "윤하얀", "전준용", "윤석현", "박희창", "진정현", "김지욱", "성재민", "강병헌", "김자연", "김영기"]
admin = ["admin"]

f = open('tq.txt', 'r', encoding='UTF8')
lines = f.read().split(',')

class UserManager:
    def __init__(self):
        self.users = {} # client side를 통해 접속한 유저 객체를 담는 변수
        self.per = True  # 커져있다 안 켜져 있다 Flag 라고 한다.

    def addUser(self, username, conn, addr):
        if username in self.users:
            conn.send('already exist.\n'.encode())
            return None
        # 비동기가 동시 처리 동기가 독립 처리
        lock.acquire() # thread의 lock객체는 공유데이터를 다룰 때 스레드를 독립성을 보장 #막아놓기 동기화되는 작업
        self.users[username] = (conn, addr) # ex) 현금 인출
        lock.release() # 독립성 보장해야하는 작업이 끝나면 release로 풀어준다.
        self.sendMessageToAll('[%s] 입장' % username)
        return username

    def removeUser(self, username):
        if username not in self.users:
            return
        lock.acquire()
        del self.users[username]
        lock.release()
        self.sendMessageToAll('[%s] 퇴장.' % username)
    def forced_exit(self, username):
        if username not in self.users: # 현재 서버가 관리하고 있는 접속자 목록 중 username이 있는지
            return
        userlist.remove(username)
        self.sendMessageToAll('[%s] 강제퇴장.' % username)
        self.users[username][0].close()

    def messageHandler(self, username, msg):   #관리자가 퇴장 시킬 수 있는 함수
        if msg[0] != '/' and self.per:
            self.sendMessageToAll('[%s] %s' % (username, msg))
            return
        else: #메세지가 /로 시작한다면

            if msg[0] + msg[1] == '/o' and username == 'admin': #admin이 /o를 입력했을 때
                self.name = msg[3] + msg[4] + msg[5]
                self.forced_exit(self.name)
            elif msg[0] + msg[1] == "/i" and username == 'admin':
                self.name = msg[3] + msg[4] + msg[5]
                userlist.append(self.name)
            elif msg[0] + msg[1] == "/n" and username == 'admin':
                tmp = msg.strip('/n')
                self.sendMessageToAll('공지사항 : ' + tmp)
            elif msg[0] + msg[1] == '/b' and username == 'admin':
                if self.per:
                    self.per = False
                    return
                else:
                    self.per = True
            elif msg[0] + msg[1] == '/w' :
                self.name = msg[3] + msg[4] + msg[5]
                tmp = msg.strip('/w')
                msg = tmp.replace(self.name, '')
                self.sendMessagetarget(self.name, username, msg)



        if msg.strip() == '/quit':
            self.removeUser(username)
            return -1

    def sendMessageToAll(self, msg):  # 입장하면 전체한테 알림이 가는 함수
        for conn, addr in self.users.values():
            conn.send(msg.encode())

    def sendMessagetarget(self, name,username, msg):
        if name in userlist or name in admin:
            self.users.get(name)[0].send((username + ">>>" + msg).encode())
            self.users.get(username)[0].send((name + ">>>" + msg).encode())
        else:
            self.users[username][0].send("없는 유저 입니다.").encode()
            return




class MyTcpHandler(socketserver.BaseRequestHandler):
    userman = UserManager()


    def handle(self):
        self.lastest = 0
        print(random.sample([1,2,3,4,5,6], k=1)) # request 객체별로 구분되는 코드 영역
        print(self,"self memory")
        print('client [%s] 연결' % self.client_address[0])

        try:
            username = self.registerUsername() # ID 처리
            print(username,":username")
            #msg = self.request.recv(1024) # 첫 마디 처리
            print(self.request)
            print(self.client_address)
            print(self.server)
            while 1:
                msg = self.request.recv(1024)
                print(msg.decode())
                x = " "
                message = str(msg, 'utf-8')

                for i in range(len(lines)):
                    if lines[i] in message:
                        self.request.send("비속어".encode())
                        x = "3"

                if x == "3":
                    continue
                if (time.time()-self.lastest >= 0.5):
                    self.lastest = time.time()
                    if self.userman.messageHandler(username, msg.decode()) == -1:
                        self.request.close()
                        break
                else:
                    self.lastest = time.time()
                    self.request.send("도배금지".encode())
                #msg = self.request.recv(1024) #메세지 받기 -> 두 번째 마디부터 나가기까지 처리한다.
        except Exception as e:
            print(e)

        print('[%s]종료' % self.client_address[0])
        self.userman.removeUser(username)
    def registerUsername(self):
        self.request.send('ID'.encode())
        while True:
            username = self.request.recv(1024)
            username = username.decode().strip()
            #####################################
            if username in userlist or username in admin:
                if self.userman.addUser(username, self.request, self.client_address):
                    return username
            else:
                self.request.send("ID 다시 입력: ".encode())

class ChatingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
def runServer():
    try:
        server = ChatingServer((HOST, PORT), MyTcpHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print('서버종료')
        server.shutdown()
        server.server_close()
runServer()