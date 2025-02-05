from dotenv import load_dotenv
import os
import random
import netifaces
import logging
import ipaddress

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ddns.log")
logging.basicConfig(filename=log_path, filemode='a', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ipv6_address_list = []
ip_address = ""

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

def get_local_ipv6_address():

    global ipv6_address_list

    if os.environ.get('ETH_LIST') :
        eth_list = os.environ.get('ETH_LIST').split(',')
    else :
        eth_list = netifaces.interfaces()

    for interface in eth_list:
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET6 in addresses:
                for addr_info in addresses[netifaces.AF_INET6]:
                    ip = addr_info.get('addr')
                    try :
                        ipv6_address = ipaddress.IPv6Address(ip.split('%')[0])
                    except ipaddress.AddressValueError:
                        return None # 视为无效地址
                    else :
                        if ipv6_address.is_global and not (ipv6_address.is_private or ipv6_address.is_reserved or ipv6_address.is_multicast or ipv6_address.is_loopback or ipv6_address.is_unspecified):
                            ipv6_address_list.append(str(ipv6_address))

def Dnspod_update_dns_record() :
    global ip_address

    from tencentcloud.common.common_client import CommonClient
    from tencentcloud.common import credential
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile

    try :
        try:
            cred = credential.Credential(
                secret_id=os.environ.get("TENCENTCLOUD_SECRETID"),
                secret_key=os.environ.get("TENCENTCLOUD_SECRETKEY"))

            httpProfile = HttpProfile()
            # 域名首段必须和下文中CommonClient初始化的产品名严格匹配
            httpProfile.endpoint = "dnspod.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile

            # 实例化要请求的common client对象，clientProfile是可选的。
            common_client = CommonClient(service="dnspod", version='2021-03-23', credential=cred, profile=clientProfile,region="")
            # 接口参数作为json字典传入，得到的输出也是json字典，请求失败将抛出异常，headers为可选参数
            common_client_output = common_client.call_json(action="ModifyDynamicDNS", params={"Domain": os.getenv('DOMAIN'),"SubDomain": os.getenv('SUBDOMAIN'), "RecordId": int(os.getenv('TENCENTCLOUD_RECORDID')), "RecordLine": "默认", "Value": ip_address})
        except TencentCloudSDKException as err:
            logging.error(f"TencentCloudSDKException: {err}")
        recordid=common_client_output["Response"]["RecordId"]
    except :
        logging.error(f"Error: Failed to update record \n common_client_output is: {common_client_output} \n", exc_info=True)

def Cloudflare_update_dns_record() :

    from cloudflare import Cloudflare

    global ip_address
    client = Cloudflare(
    api_email=os.environ.get("CLOUDFLARE_EMAIL"), 
    api_key=os.environ.get("CLOUDFLARE_API_KEY"), 
    )
    try :
        record_response = client.dns.records.edit(
            dns_record_id=os.environ.get("CLOUDFLARE_RECORD_ID"),
            zone_id=os.environ.get("CLOUDFLARE_ZONE_ID"),
            content=ip_address,
        )
        record_response.content
    except Exception as e:
        logging.error("Error: Failed to update record \n", exc_info=True)



def main():
    
    ipfile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_ipv6_address.txt")
    get_local_ipv6_address()
    with open(ipfile_path, 'r') as f :
        last_ipv6_address = f.read().strip()

    if last_ipv6_address in ipv6_address_list :
        logging.info("IPv6 address not changed.")
        exit(0)
    
    else :
        global ip_address
        ip_address = random.choice(ipv6_address_list)

        match os.getenv('DDNS_PROVIDER') :
            case 'dnspod' :
                Dnspod_update_dns_record()
            case 'cloudflare' :
                Cloudflare_update_dns_record()
            case None :
                logging.error("DDNS_PROVIDER not set in environment variables.")
                exit(1)
            case _:
                logging.error("Invalid DDNS_PROVIDER in environment variables.")
                exit(1)

        with open(ipfile_path, 'w') as f :
            f.write(ip_address)

        logging.info("DNS record updated successfully.")
        exit(0)

main()
    