import argparse, socket
import codecs, binascii

MAX_BYTES = 548

def server():
    sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) # 使用UPD協定
    sock.bind( ( '', 67 ) ) # DHCP server 使用的port為67
    print( 'Listening at {}'.format(sock.getsockname()) )

    while True:
        data, address = sock.recvfrom(MAX_BYTES)
        print( 'The client at {}'.format( address ) )
        print( 'Reveive data: {}'.format( data ) )

def client():
    sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    sock.setsockopt( socket.SOL_SOCKET, socket.SO_BROADCAST, 1 )
    sock.bind( ( '0.0.0.0', 68 ) ) # DHCP client則綁定port 68
    data = bytes.fromhex( '01010600' ) # test
    print( 'Send data: {}'.format( data ) )
    sock.sendto( data, ( '127.0.0.1', 67 ) )
    print( 'The OS assign me the address {}'.format( sock.getsockname() ) )



if __name__ == '__main__':
    # 採用和書本範例相同的方法,用參數來決定使用的功能
    # client表示請求IP位置的一方,server則是根據傳近來的請求給予IP位置 
    choices = {'client': client, 'server': server}
    parser = argparse.ArgumentParser(description='Send and receive DHCP request')
    parser.add_argument('role', choices=choices, help='which role to play')

    args = parser.parse_args()
    function = choices[args.role]
    function( )
