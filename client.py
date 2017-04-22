import socket
import sys
import random
import binascii
import logging
from optparse import OptionParser

usage = "usage: %prog -H arg1 -P arg2"
parser = OptionParser(usage=usage)
parser.add_option("-H", "--host", help="target's host", metavar="HOST",dest="host",default="localhost")  
parser.add_option("-P", "--port", help="target's port", metavar="PORT",dest="port",default=9999,type=int)   
(opts, args) = parser.parse_args()
# try:
#     opts, args=getopt.getopt(sys.argv[1:],"h:p:",["host=","port="])
# except getopt.GetoptError as e:
#     print(e)
#     sys.exit()
# for name,value in opts:
#     if name in ("--host","-h"):
#         host=value
#     if name in ("--port","-p"):
#         port=value
    # if name in ("--command","-c"):
    #     command=value

class udpclient:
    def __init__(self,host,port):
        self.serveraddress=(host,port)
        self.clientsocket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    @staticmethod
    def get_nat_type():
        __version__ = "0.0.4"

        log = logging.getLogger("pystun")


        def enable_logging():
            logging.basicConfig()
            log.setLevel(logging.DEBUG)

        stun_servers_list = (
            "stun.ekiga.net",
            'stunserver.org',
            'stun.ideasip.com',
            'stun.softjoys.com',
            'stun.voipbuster.com',
        )

        #stun attributes
        MappedAddress = '0001'
        ResponseAddress = '0002'
        ChangeRequest = '0003'
        SourceAddress = '0004'
        ChangedAddress = '0005'
        Username = '0006'
        Password = '0007'
        MessageIntegrity = '0008'
        ErrorCode = '0009'
        UnknownAttribute = '000A'
        ReflectedFrom = '000B'
        XorOnly = '0021'
        XorMappedAddress = '8020'
        ServerName = '8022'
        SecondaryAddress = '8050'  # Non standard extention

        #types for a stun message
        BindRequestMsg = '0001'
        BindResponseMsg = '0101'
        BindErrorResponseMsg = '0111'
        SharedSecretRequestMsg = '0002'
        SharedSecretResponseMsg = '0102'
        SharedSecretErrorResponseMsg = '0112'

        dictAttrToVal = {'MappedAddress': MappedAddress,
                         'ResponseAddress': ResponseAddress,
                         'ChangeRequest': ChangeRequest,
                         'SourceAddress': SourceAddress,
                         'ChangedAddress': ChangedAddress,
                         'Username': Username,
                         'Password': Password,
                         'MessageIntegrity': MessageIntegrity,
                         'ErrorCode': ErrorCode,
                         'UnknownAttribute': UnknownAttribute,
                         'ReflectedFrom': ReflectedFrom,
                         'XorOnly': XorOnly,
                         'XorMappedAddress': XorMappedAddress,
                         'ServerName': ServerName,
                         'SecondaryAddress': SecondaryAddress}

        dictMsgTypeToVal = {
            'BindRequestMsg': BindRequestMsg,
            'BindResponseMsg': BindResponseMsg,
            'BindErrorResponseMsg': BindErrorResponseMsg,
            'SharedSecretRequestMsg': SharedSecretRequestMsg,
            'SharedSecretResponseMsg': SharedSecretResponseMsg,
            'SharedSecretErrorResponseMsg': SharedSecretErrorResponseMsg}

        dictValToMsgType = {}

        dictValToAttr = {}

        Blocked = "Blocked"
        OpenInternet = "Open Internet"
        FullCone = "Full Cone"
        SymmetricUDPFirewall = "Symmetric UDP Firewall"
        RestrictNAT = "Restrict NAT"
        RestrictPortNAT = "Restrict Port NAT"
        SymmetricNAT = "Symmetric NAT"
        ChangedAddressError = "Meet an error, when do Test1 on Changed IP and Port"


        def _initialize():
            items = list(dictAttrToVal.items())
            for i in range(len(items)):
                dictValToAttr.update({items[i][1]: items[i][0]})
            items = list(dictMsgTypeToVal.items())
            for i in range(len(items)):
                dictValToMsgType.update({items[i][1]: items[i][0]})


        def gen_tran_id():
            a = ''
            for i in range(32):
                a += random.choice('0123456789ABCDEF')  # RFC3489 128bits transaction ID
            #return binascii.a2b_hex(a)
            return a


        def stun_test(sock, host, port, source_ip, source_port, send_data=""):
            retVal = {'Resp': False, 'ExternalIP': None, 'ExternalPort': None,
                      'SourceIP': None, 'SourcePort': None, 'ChangedIP': None,
                      'ChangedPort': None}
            str_len = "%#04d" % (len(send_data) / 2)
            tranid = gen_tran_id()
            str_data = ''.join([BindRequestMsg, str_len, tranid, send_data])
            data = binascii.a2b_hex(str_data)
            recvCorr = False
            while not recvCorr:
                recieved = False
                count = 3
                while not recieved:
                    log.debug("sendto %s" % str((host, port)))
                    try:
                        # print(host,port)
                        sock.sendto(data, (host, port))
                    except socket.gaierror:
                        retVal['Resp'] = False
                        return retVal
                    try:
                        buf, addr = sock.recvfrom(2048)
                        log.debug("recvfrom: %s" % str(addr))
                        recieved = True
                    except Exception:
                        recieved = False
                        if count > 0:
                            count -= 1
                        else:
                            retVal['Resp'] = False
                            return retVal
                msgtype = binascii.b2a_hex(buf[0:2])
                bind_resp_msg = dictValToMsgType[msgtype.decode()] == "BindResponseMsg"
                # print(bind_resp_msg)
                tranid_match = tranid.upper().encode() == binascii.b2a_hex(buf[4:20]).upper()
                # print(binascii.b2a_hex(buf[4:20]).upper())
                # print(tranid.upper())
                # print(tranid_match)
                if bind_resp_msg and tranid_match:
                    recvCorr = True
                    retVal['Resp'] = True
                    len_message = int(binascii.b2a_hex(buf[2:4]), 16)
                    len_remain = len_message
                    base = 20
                    while len_remain:
                        attr_type = binascii.b2a_hex(buf[base:(base + 2)])
                        attr_len = int(binascii.b2a_hex(buf[(base + 2):(base + 4)]),
                                       16)
                        if attr_type == MappedAddress.encode():  # first two bytes: 0x0001
                            port = int(binascii.b2a_hex(buf[base + 6:base + 8]), 16)
                            ip = ".".join([
                            str(int(binascii.b2a_hex(buf[base + 8:base + 9]), 16)),
                            str(int(binascii.b2a_hex(buf[base + 9:base + 10]), 16)),
                            str(int(binascii.b2a_hex(buf[base + 10:base + 11]), 16)),
                            str(int(binascii.b2a_hex(buf[base + 11:base + 12]), 16))])
                            retVal['ExternalIP'] = ip
                            retVal['ExternalPort'] = port
                        if attr_type == SourceAddress.encode():
                            port = int(binascii.b2a_hex(buf[base + 6:base + 8]), 16)
                            ip = ".".join([
                            str(int(binascii.b2a_hex(buf[base + 8:base + 9]), 16)),
                            str(int(binascii.b2a_hex(buf[base + 9:base + 10]), 16)),
                            str(int(binascii.b2a_hex(buf[base + 10:base + 11]), 16)),
                            str(int(binascii.b2a_hex(buf[base + 11:base + 12]), 16))])
                            retVal['SourceIP'] = ip
                            retVal['SourcePort'] = port
                        if attr_type == ChangedAddress.encode():
                            port = int(binascii.b2a_hex(buf[base + 6:base + 8]), 16)
                            ip = ".".join([
                            str(int(binascii.b2a_hex(buf[base + 8:base + 9]), 16)),
                            str(int(binascii.b2a_hex(buf[base + 9:base + 10]), 16)),
                            str(int(binascii.b2a_hex(buf[base + 10:base + 11]), 16)),
                            str(int(binascii.b2a_hex(buf[base + 11:base + 12]), 16))])
                            retVal['ChangedIP'] = ip
                            # print(ip)
                            retVal['ChangedPort'] = port
                        #if attr_type == ServerName:
                            #serverName = buf[(base+4):(base+4+attr_len)]
                        base = base + 4 + attr_len
                        len_remain = len_remain - (4 + attr_len)
            #s.close()
            return retVal


        def get_nat_type(s, source_ip, source_port, stun_host=None, stun_port=3478):
            _initialize()
            port = stun_port
            log.debug("Do Test1")
            resp = False
            if stun_host:
                ret = stun_test(s, stun_host, port, source_ip, source_port)
                resp = ret['Resp']
            else:
                for stun_host in stun_servers_list:
                    log.debug('Trying STUN host: %s' % stun_host)
                    ret = stun_test(s, stun_host, port, source_ip, source_port)
                    resp = ret['Resp']
                    if resp:
                        break
            if not resp:
                return Blocked, ret
            log.debug("Result: %s" % ret)
            exIP = ret['ExternalIP']
            exPort = ret['ExternalPort']
            changedIP = ret['ChangedIP']
            changedPort = ret['ChangedPort']
            if ret['ExternalIP'] == source_ip:
                changeRequest = ''.join([ChangeRequest, '0004', "00000006"])
                ret = stun_test(s, stun_host, port, source_ip, source_port,
                                changeRequest)
                if ret['Resp']:
                    typ = OpenInternet
                else:
                    print("firewall")
                    typ = SymmetricUDPFirewall
            else:
                changeRequest = ''.join([ChangeRequest, '0004', "00000006"])
                log.debug("Do Test2")
                ret = stun_test(s, stun_host, port, source_ip, source_port,
                                changeRequest)
                log.debug("Result: %s" % ret)
                if ret['Resp']:
                    typ = FullCone
                else:
                    log.debug("Do Test1")
                    # print(changedIP)
                    ret = stun_test(s, changedIP, changedPort, source_ip, source_port)
                    log.debug("Result: %s" % ret)
                    if not ret['Resp']:
                        typ = ChangedAddressError
                    else:
                        if exIP == ret['ExternalIP'] and exPort == ret['ExternalPort']:
                            changePortRequest = ''.join([ChangeRequest, '0004', "00000002"])
                            log.debug("Do Test3")
                            ret = stun_test(s, changedIP, port, source_ip, source_port, changePortRequest)
                            log.debug("Result: %s" % ret)
                            if ret['Resp'] == True:
                                typ = RestrictNAT
                            else:
                                typ = RestrictPortNAT
                        else:
                            typ = SymmetricNAT
            return typ, ret


        def get_ip_info(source_ip="0.0.0.0", source_port=54320, stun_host=None,
                        stun_port=3478):
            socket.setdefaulttimeout(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((source_ip, source_port))
            nat_type, nat = get_nat_type(s, source_ip, source_port,
                                         stun_host=stun_host, stun_port=stun_port)
            external_ip = nat['ExternalIP']
            external_port = nat['ExternalPort']
            s.close()
            socket.setdefaulttimeout(None)
            return nat_type, external_ip, external_port


        def main():
            nat_type, external_ip, external_port = get_ip_info()
            # print("NAT Type:", nat_type)
            # print("External IP:", external_ip)
            # print("External Port:", external_port)
            return nat_type

        return main()

    def start(self):
        nat_type=self.get_nat_type()
        data={
            'command':'login',
            'nat_type':nat_type,
        }
        self.clientsocket.sendto(str(data).encode(),self.serveraddress)
        res=self.clientsocket.recvfrom(2048)
        print(res)
        while True:
            command=input("please enter the command:")
            operation={
                "login":self.login,
                "showusers":self.showusers,
                "connect":self.connect,
                "logout":self.logout,
            }
            if command=="exit":
                break
            else:
                operation.get(command,self.error)()
        self.close()

    def showusers(self):
        try:
            data={
                "command":"showusers",
            }
            self.clientsocket.sendto(str(data).encode(),self.serveraddress)
            res=self.clientsocket.recvfrom(2048)
            print(res)
        except Exception as e:
            print(e)

    def error(self):
        print('error')
        sys.exit()
        # if not res:
        #     clientsocket.close()

    def logout(self):
        data={
            "command":"logout",
        }
        self.clientsocket.sendto(str(data).encode(),self.serveraddress)
        res=self.clientsocket.recvfrom(2048)
        print(res)

    def close(self):
        try:
            self.clientsocket.close()
        except Exception as e:
            print(e)

    def connect(self):
        data={
        'command':'login',
        'nat_type':nat_type,
        }

if __name__ == "__main__":
    # HOST,PORT="localhost",9999
    client=udpclient(opts.host,opts.port)
    try:
        client.start()
        # client.get_nat_type()
    except Exception as e:
        print(e)