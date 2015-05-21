import asyncio, argparse, queue

class User:
  def __init__( self, username, password ):
    self.username = username
    self.password = password
    self.status = "logout"
    self.messageQueue = queue.Queue()

  def login( self, transport ):
    self.transport = transport
    self.status = "login"

  def logout( self ):
    self.status = "logoout"
    

# ==============================================


class ChatServer(asyncio.Protocol):
  users = {} # 該server的所有使用者,以static變數的方式儲存
  currentUser = None

  def connection_made( self, transport ):
    self.transport = transport
    self.address = transport.get_extra_info( 'peername' )
    self.data = b''
    print( 'Accepted connection from {}'.format(self.address) )

  def data_received( self, data ):
    dataTokens = data.decode().split( ' ' )
    if self.currentUser == None: # 確認登入狀態,如果尚未登入的話即刻開始驗證使用者
      if dataTokens[0] == 'login' and len( dataTokens ) == 3:
      # 確認是否為login行為,並且是否參數為三個(login, username, password)
        username = dataTokens[1]
        password = dataTokens[2]
        if username in list( ChatServer.users.keys() ) and ChatServer.users[username].password == password:
        # 卻認為登入行為,修改狀態為登入
          self.currentUser = ChatServer.users[username]
          ChatServer.users[username].login( self.transport )
          sendData = 'Login success'
          print( 'User {} login.'.format( username ) )
          self.transport.write( sendData.encode() )
          # 如果有離線訊息,則一併傳送過去
          while not self.currentUser.messageQueue.empty():
            sendData = '\n Offline message:' + self.currentUser.messageQueue.get()
            self.transport.write( sendData.encode() )
            
        else:
        # 如果帳號密碼不正確,則送出錯誤息,並且主動斷開連結
          print( '{} name or password is invalid'.format( username ) )
          sendData = 'Login Faild'
          self.transport.write( sendData.encode() )
          self.transport.close()

      else:
      # 如果連login格式都不正確,直接卻認為登入失敗
        print( '{} syntax error'.format( self.address ) )
        sendData = 'Login Faild'
        self.transport.write( sendData.encode() )
        self.transport.close()

    else: # 這邊是處理已經登入的連線狀況
      if dataTokens[0] == 'logout': # 使用者輸入logout指令,進行登出並斷開連線
        print( 'User {} loout'.format( self.currentUser.username ) )
        # 送出成功登出的訊息,隨即斷開連線
        sendData = 'Logout success!'
        self.transport.write( sendData.encode() )
        self.currentUser.logout()
        self.transport.close()

      elif dataTokens[0] == 'send' and len(dataTokens) >= 3:
      # 發送訊息給指定目的的指令,此指令必定包含三個區段
        # 由於要保留完整字串,所以token重切成三段
        dataTokens = data.decode().split( ' ', 2 )
        destUser = dataTokens[1]
        message = dataTokens[2]
        if destUser in list( ChatServer.users.keys() ): # 確定真有此人
          sendData = '{} says :{}'.format( self.currentUser.username, message )
          ChatServer.send_to_user( ChatServer.users[destUser], sendData )
        else: # 找不到該用戶
          sendData = '{} doesn\'t exist.'.destUser
          self.transport.write( sendData.encode() )
      elif dataTokens[0] == 'checkname' and len(dataTokens) == 2:
      # 用來確認某個指定名子的狀態
        destUser = dataTokens[1]
        if destUser in list( ChatServer.users.keys() ): # 確定真有此人
          if( ChatServer.users[destUser].status == 'login' ):
            sendData = '{}: online'.format(destUser)
          else:
            sendData = '{}: offline'.format(destUser)
        else:
          sendData = '{} doesn\'t exist.'.format( destUser )
        self.transport.write( sendData.encode() )

      elif dataTokens[0] == 'listuser' and len(dataTokens) == 1:
      # 列出所有線上使用者
        onlineUsers = []
        for username in list( ChatServer.users.keys()):
          if ChatServer.users[username].status == 'login':
            onlineUsers.append(username)

        sendData = ''
        for index, name in enumerate(onlineUsers):
          sendData = sendData + name
          if  index != len(onlineUsers) - 1:
            sendData = sendData + '\n'
        self.transport.write( sendData.encode() )

      elif dataTokens[0] == 'broadcast' and len(dataTokens) >= 2:
      # 廣播指令,將訊息傳送給所有使用者
        dataTokens = data.decode().split( ' ', 1 )
        message = dataTokens[1] # 取得訊息區段
        sendData = self.currentUser.username + ' broadcast: ' + message
        allUsers = list( ChatServer.users.keys() )
        for name in allUsers:
          ChatServer.send_to_user( ChatServer.users[name], sendData )
      else:
      # 所有指令接部不合格式,回傳正確格式
        sendData = 'Invalid instruction.\n'
        sendData = sendData + '>listuser\n'
        sendData = sendData + '>checkname [username]\n'
        sendData = sendData + '>send [username] [message]\n'
        sendData = sendData + '>broadcast [message]\n'
        sendData = sendData + '>logout'
        self.transport.write( sendData.encode() )

  def send_to_user( user, sendData ):
    if user.status == 'login':
      user.transport.write( sendData.encode() )
    else:
      print( "queue data:" + sendData )
      user.messageQueue.put( sendData )

  def connection_lost( self, exc ):
    if exc:
      print( 'Client {} error: {}'. format(self.address, exc) )
    elif self.data:
      print( 'Client {} sent {} but then closed'.format(self.address, self.data) )
    else:
      print( 'Client {} closed socket'.format(self.address) )

# ==============================================

def parse_command_line(description):
  parser = argparse.ArgumentParser(description)
  parser.add_argument( 'host', help = 'IP or hostname' )
  parser.add_argument( '-p', metavar = 'port', type=int, default = 1060,
                       help = 'TCP port (default 1060)' )
  args = parser.parse_args()
  address = ( args.host, args.p )
  return address


if __name__ == '__main__':
  address = parse_command_line( 'Asyncio chat server using callbacks' )
  loop = asyncio.get_event_loop()
  # 內建兩名使用者
  ChatServer.users['john'] = User( 'john', '1234' )
  ChatServer.users['mary'] = User( 'mary', '5678' )

  coro = loop.create_server( ChatServer, *address )
  server = loop.run_until_complete(coro)
  print( 'Listening at {}'.format( address ) )
  try:
    loop.run_forever()
  except KeyboardInterrupt:
    pass
