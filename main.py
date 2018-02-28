#!/usr/bin/env python
# encoding: utf-8
import os
import sys
import time
import json
import smtplib
import datetime
from configparser import ConfigParser
from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from QcloudApi.qcloudapi import QcloudApi
from email.mime.text import MIMEText
from email.header import Header

reload(sys)
sys.setdefaultencoding("utf-8")

ALIYUNCONFIGFILE = os.getcwd() + '/aliyun-config.ini'
QCLOUDCONFIGFILE = os.getcwd() + '/qcloud-config.ini'
RESULT = os.getcwd() + '/alertcloud.log'

today = datetime.datetime.now().strftime('%Y-%m-%d')
todayStr = today.split('-')
expired_dn = datetime.datetime(int(todayStr[0]), int(todayStr[1]), int(todayStr[2]))

from_addr = 'mikemike@test.com'
to_addr = ['mike@test.com']
#to_addr = ['luwen@jf.com']
password = 'xxxxxxxx'
smtpServer = 'smtp.jf.com'

if os.path.exists(RESULT):
    os.remove(RESULT)
f = open(RESULT,'a')



def aliyun_ecs_monitor(SecretId,SecretKey,RegionId):
    #ecs_list = []
    clt = client.AcsClient(SecretId,SecretKey,RegionId)

    # 设置参数
    request = DescribeInstancesRequest.DescribeInstancesRequest()
    request.set_accept_format('json')
    request.add_query_param('RegionId', RegionId)
    request.add_query_param('PageNumber', 1)
    request.add_query_param('PageSize', 100)

    # 发起请求
    response = clt.do_action(request)

    str_response = json.loads(response)
    return str_response['Instances']['Instance']
    #for inst in str_response['Instances']['Instance']:
    #    tuple_ecs = (inst['InstanceId'],inst['ExpiredTime'],inst['RegionId'])
    #    ecs_list.append(tuple_ecs)
    #return ecs_list

def qcloud_ecs_monitor(SecretId,SecretKey,Region):
    module = 'cvm'
    action = 'DescribeInstances'
    action_params = {
        'limit':100,
    }
    config = {
        'Region': Region,
        'secretId': SecretId,
        'secretKey': SecretKey,
    }

    try:
        service = QcloudApi(module, config)
        #print service.generateUrl(action, action_params)
        inst = json.loads(service.call(action, action_params))
        return inst['instanceSet']
    except Exception as e:
        import traceback
        print('traceback.format_exc():\n%s' % traceback.format_exc())


def utc2local(utc_st):
    UTC_FORMAT = "%Y-%m-%dT%H:%MZ"
    expired_utc = datetime.datetime.strptime(utc_st, UTC_FORMAT)
    now_stamp = time.time()
    local_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = expired_utc + offset
    expired_local = local_st.strftime('%Y-%m-%d')
    return expired_local

def time2day(expired_qcloud):
    LOCAL_FORMAT = "%Y-%m-%d %H:%M:%S"
    expired_qcloud = datetime.datetime.strptime(expired_qcloud, LOCAL_FORMAT)
    expired_day_qcloud = expired_qcloud.strftime('%Y-%m-%d')
    return expired_day_qcloud

def sendmail(from_addr,password,to_addr,smtpServer,subject,content):
    from_addr = from_addr
    password = password
    to_addr = to_addr
    smtp_server = smtpServer
    msg = MIMEText(content,'plain','utf-8')
    msg['From'] = from_addr
    msg['To'] = ','.join(to_addr)
    msg['Subject'] = subject
    server = smtplib.SMTP(smtp_server,25)
    #server.set_debuglevel(1)
    server.login(from_addr,password)
    server.sendmail(from_addr,to_addr,msg.as_string())
    server.quit()


if __name__ == '__main__':
    #aliyun
    cfg = ConfigParser()
    cfg.read(ALIYUNCONFIGFILE)
    for account in cfg.sections():
        UserName = str(cfg.get(account,"UserName"))
        SecretId = str(cfg.get(account,"SecretId"))
        SecretKey = str(cfg.get(account,"SecretKey"))
        RegionIds = str(cfg.get(account,"RegionId")).split(",")
        for RegionId in RegionIds:
            for inst in aliyun_ecs_monitor(SecretId,SecretKey,RegionId):
                lanIp_aliyun = '-'.join(inst['VpcAttributes']['PrivateIpAddress']['IpAddress'])
                InstanceId_aliyun = inst['InstanceId']
                expired_aliyun_time = utc2local(inst['ExpiredTime'])
                expiredStr_aliyun = expired_aliyun_time.split('-')
                expired_dw_aliyun = datetime.datetime(int(expiredStr_aliyun[0]), int(expiredStr_aliyun[1]), int(expiredStr_aliyun[2]))
                periodTime_aliyun = (expired_dw_aliyun - expired_dn).days
                if periodTime_aliyun < 7 and periodTime_aliyun >= -3:
                    f.write("阿里云%s账号下服务器%s-%s还有%s天过期，请注意续费\n" %(UserName,InstanceId_aliyun,lanIp_aliyun,periodTime_aliyun))
                    #sendmail(from_addr,password,to_addr,smtpServer,subject,content)

    #qcloud
    cfg = ConfigParser()
    cfg.read(QCLOUDCONFIGFILE)
    for account in cfg.sections():
        UserName = str(cfg.get(account,"UserName"))
        SecretId = str(cfg.get(account,"SecretId"))
        SecretKey = str(cfg.get(account,"SecretKey"))
        Regions = str(cfg.get(account,"Region")).split(",")
        for Region in Regions:
            for cvm in qcloud_ecs_monitor(SecretId,SecretKey,Region):
                InstanceId_qcloud = cvm['instanceId']
                lanIp_qcloud = cvm['lanIp']
                expired_qcloud_time = time2day(cvm['deadlineTime'])
                expiredStr_qcloud = expired_qcloud_time.split('-')
                expired_dw_qcloud = datetime.datetime(int(expiredStr_qcloud[0]), int(expiredStr_qcloud[1]), int(expiredStr_qcloud[2]))
                periodTime_qcloud = (expired_dw_qcloud - expired_dn).days
                if periodTime_qcloud < 7 and periodTime_aliyun >= -3:
                    f.write("腾讯云%s账号下服务器%s-%s还有%s天过期，请注意续费\n" %(UserName,InstanceId_qcloud,lanIp_qcloud,periodTime_qcloud))
    f.close()
    #sendmail
    subject = "云服务器即将过期服务器列表邮件"
    filecon = open(RESULT,"rb")
    content = filecon.read()
    sendmail(from_addr,password,to_addr,smtpServer,subject,content)
    filecon.close()
