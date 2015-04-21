import argparse, socket
import codecs, binascii
import random
import uuid

MAX_BYTES = 548

def server():
    sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) # 使用UPD協定
    sock.setsockopt( socket.SOL_SOCKET, socket.SO_BROADCAST, 1 )
    sock.bind( ( '', 67 ) ) # DHCP server 使用的port為67
    print( 'Listening at {}'.format(sock.getsockname()) )

    while True:
        receiveData, address = sock.recvfrom( MAX_BYTES )
        print( 'Reveive data: {}'.format( receiveData ) )
        if isDHCPDISCOVERmsg( receiveData[240:len(receiveData)] ):
            print( 'Is \"DHCP Discover\"!!!' )
            requestIP = getRequestIP( receiveData[240:len(receiveData)] )
            hostIP = socket.inet_aton( socket.gethostbyname( socket.gethostname() ) )
            sendData = makeDHCPOFFERmsg( receiveData[4:8], requestIP, receiveData[28:44], hostIP )
            sock.sendto( sendData, ( '255.255.255.255', 68 ) )
        elif isDHCPREQUESTmsg( receiveData[240:len(receiveData)] ):
            print( 'Is\"DHCP Request\"!!!' )
            dhcpServerIP = getDHCPServerIP( receiveData[240:len(receiveData)] )
            requestIP = getRequestIP( receiveData[240:len(receiveData)] )
            sendData = makeDHCPACKmsg( receiveData[4:8], requestIP, receiveData[28:44], dhcpServerIP )
            sock.sendto( sendData, ( '255.255.255.255', 68 ) )
            
         

def client():
    sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    sock.setsockopt( socket.SOL_SOCKET, socket.SO_BROADCAST, 1 )
    sock.bind( ( '0.0.0.0', 68 ) ) # DHCP client則綁定port 68
    sendData = makeDHCPDISCOVERmsg()
    print( 'Send data: {}'.format( sendData ) )
    sock.sendto( sendData, ( '255.255.255.255', 67 ) )
    receiveData, address = sock.recvfrom( MAX_BYTES )
    if isDHCPOFFERmsg( receiveData[240:len(receiveData)] ):
        print( 'Is \"DHCP Offer\"!!!' )
        dhcpServerIP = getDHCPServerIP( receiveData[240:len(receiveData)] )
        sendData = makeDHCPREQUESTmsg( receiveData[4:8], dhcpServerIP )
        sock.sendto( sendData, ( '255.255.255.255', 67 ) )

# ========================================================

def makeDHCPDISCOVERmsg():
    data = bytes([0x01, 0x01, 0x06, 0x00])
    data = data + xid()
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # SECS FLAGS
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # CIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # YIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # SIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # GIADDR
    data = data + uuid.getnode().to_bytes( 6, 'big') # CHADDR
    data = data + bytes( [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] )
    data = data + bytes( 192 ) # BOOTP legacy
    data = data + bytes( [0x63, 0x82, 0x53, 0x63]) # Magic Cookie
    data = data + bytes( [53, 1, 1] ) # DHCP Discover
    data = data + bytes( [50, 4, 192, 168, 1, 100] ) #IP requested
    data = data + bytes( [0xff] ) # end option

    return data
    
# ========================================================

def makeDHCPOFFERmsg( xid, requestIP, chaddr, hostIP ):
    data = bytes([0x02, 0x01, 0x06, 0x00])
    data = data + xid
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # SECS FLAGS
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # CIADDR
    data = data + requestIP # YIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # SIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # GIADDR
    data = data + chaddr # CHADDR
    data = data + bytes( 192 ) # BOOTP legacy
    data = data + bytes( [0x63, 0x82, 0x53, 0x63]) # Magic Cookie
    data = data + bytes( [53, 1, 2] ) # DHCP Offer
    data = data + bytes( [1, 4, 255, 255, 255, 0] ) #subnet mask
    data = data + bytes( [51,4] ) + hostIP # router
    data = data + bytes( [51, 4] ) + (86400).to_bytes( 4, 'big' ) # IP lease time
    data = data + bytes( [54,4] ) + hostIP
    data = data + bytes( [0xff] ) # end option

    return data
    
# ========================================================

def makeDHCPREQUESTmsg( xid, dhcpServerIP):
    data = bytes([0x01, 0x01, 0x06, 0x00])
    data = data + xid
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # SECS FLAGS
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # CIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # YIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # SIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # GIADDR
    data = data + uuid.getnode().to_bytes( 6, 'big') # CHADDR
    data = data + bytes( [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] )
    data = data + bytes( 192 ) # BOOTP legacy
    data = data + bytes( [0x63, 0x82, 0x53, 0x63]) # Magic Cookie
    data = data + bytes( [53, 1, 3] ) # DHCP Discover
    data = data + bytes( [50, 4, 192, 168, 1, 100] ) #IP requested
    data = data + bytes( [54, 4] ) + dhcpServerIP # dhcp server IP
    data = data + bytes( [0xff] ) # end option

    return data
    
# ========================================================

def makeDHCPACKmsg( xid, requestIP, chaddr, dhcpServerIP ):
    data = bytes([0x02, 0x01, 0x06, 0x00])
    data = data + xid
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # SECS FLAGS
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # CIADDR
    data = data + requestIP # YIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # SIADDR
    data = data + bytes( [0x00, 0x00, 0x00, 0x00] ) # GIADDR
    data = data + chaddr # CHADDR
    data = data + bytes( 192 ) # BOOTP legacy
    data = data + bytes( [0x63, 0x82, 0x53, 0x63]) # Magic Cookie
    data = data + bytes( [53, 1, 5] ) # DHCP Offer
    data = data + bytes( [1, 4, 255, 255, 255, 0] ) #subnet mask
    data = data + bytes( [51,4] ) + dhcpServerIP # router
    data = data + bytes( [51, 4] ) + (86400).to_bytes( 4, 'big' ) # IP lease time
    data = data + bytes( [54,4] ) + dhcpServerIP
    data = data + bytes( [0xff] ) # end option

    return data
    
# ========================================================
def isDHCPDISCOVERmsg( dhcpoptions ):
    index = 0
    optLen = len(dhcpoptions)
    while index < optLen and dhcpoptions[index] != 0xff:
        if dhcpoptions[index] == 53 and dhcpoptions[index+2] == 1:
            return True
        else:
            index = index + 2 + dhcpoptions[index+1]

    return False

# ========================================================

def isDHCPOFFERmsg( dhcpoptions ):
    index = 0
    optLen = len(dhcpoptions)
    while index < optLen and dhcpoptions[index] != 0xff:
        print( dhcpoptions[index] )
        print( dhcpoptions[index+2] )
        if dhcpoptions[index] == 53 and dhcpoptions[index+2] == 2:
            return True
        else:
            index = index + 2 + dhcpoptions[index+1]

    return False

# ========================================================

def isDHCPREQUESTmsg( dhcpoptions ):
    index = 0
    optLen = len(dhcpoptions)
    while index < optLen and dhcpoptions[index] != 0xff:
        if dhcpoptions[index] == 53 and dhcpoptions[index+2] == 3:
            return True
        else:
            index = index + 2 + dhcpoptions[index+1]

    return False

# ========================================================

def getRequestIP( dhcpoptions ):
    index = 0
    optLen = len(dhcpoptions)
    while index < optLen and dhcpoptions[index] != 0xff:
        if dhcpoptions[index] == 50 and dhcpoptions[index+1] == 4:
            return dhcpoptions[index+2:index+6]
        else:
            index = index + 2 + dhcpoptions[index+1]

    return False

# ========================================================

def getDHCPServerIP( dhcpoptions ):
    index = 0
    optLen = len(dhcpoptions)
    while index < optLen and dhcpoptions[index] != 0xff:
        if dhcpoptions[index] == 54 and dhcpoptions[index+1] == 4:
            return dhcpoptions[index+2:index+6]
        else:
            index = index + 2 + dhcpoptions[index+1]

    return False

# ========================================================

def xid():
    return bytes( random.getrandbits(8) for i in range(4) )


if __name__ == '__main__':
    # 採用和書本範例相同的方法,用參數來決定使用的功能
    # client表示請求IP位置的一方,server則是根據傳近來的請求給予IP位置 
    choices = {'client': client, 'server': server}
    parser = argparse.ArgumentParser(description='Send and receive DHCP request')
    parser.add_argument('role', choices=choices, help='which role to play')

    args = parser.parse_args()
    function = choices[args.role]
    function( )
