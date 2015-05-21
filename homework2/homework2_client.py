import asyncio, argparse, socket
import sys, time, _thread, os

def handleConversationThread( sock, address, status ):
# 用以接收訊息並且印出的thread
  try:
    while True:
      data = sock.recv(4096)
      if not data:
        raise EOFError( 'socket closed' )
      else:
        print( data.decode() )
  except EOFError:
    print( 'Client socket to {} has closed'.format( address ) )
  except Exception as e:
    print( 'Client {} error: {}'.format( address, e ) )
  finally:
    sock.close()
    status['still_alive'] = False
    

def receveData( sock ):
  data = sock.recv( 4096 )
  

def client( address, cause_error=False):
  sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
  sock.connect(address)
  username = input( "> Username: " )
  os.system( "stty -echo" )
  password = input( "> password: " )
  print( '\n' )
  os.system( "stty echo" )
  sendData = 'login' + ' ' + username + ' ' + password
  sock.sendall( sendData.encode() )

  status = {}
  status['still_alive'] = True # 這個值是為了要在sock斷開連結後結束所有程式
  _thread.start_new_thread( handleConversationThread, ( sock, address, status ) )

  inputString = input( ">" )
  # 登入完成,開始輸入指令
  while status['still_alive']:
    inputString = input( ">" )
    if status['still_alive']:
      sock.sendall( inputString.encode() )
    else:
      return

# =================================

if __name__ == '__main__':
  parser = argparse.ArgumentParser( description = 'Asyncio Chat client' )
  parser.add_argument( 'host', help = 'IP or hostname' )
  parser.add_argument( '-p', metavar = 'port', type = int, default = 1060,
                       help = 'TCP port (default 1060)' )
  parser.add_argument( '-e', action = 'store_true', help = 'cause an error' )
  args = parser.parse_args()
  address = ( args.host, args.p ) # ip address and port

  client( address, args.e )
