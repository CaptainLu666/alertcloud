#!/usr/bin/env python
# encoding: utf-8
import os
import sys
import time
import json
import smtplib
import datetime
from ecs import AliEcs,QcloudCvm
from rds import AliRds,QcloudCdb
from configparser import ConfigParser
from aliyunsdkcore import client
from aliyunsdkcore.request import RpcRequest
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526 import DescribeInstanceAutoRenewAttributeRequest
from aliyunsdkrds.request.v20140815 import DescribeInstanceAutoRenewalAttributeRequest
from QcloudApi.qcloudapi import QcloudApi
from email.mime.text import MIMEText
from email.header import Header

reload(sys)
sys.setdefaultencoding("utf-8")

#ALIYUNCONFIGFILE = os.getcwd() + '/aliyun-config.ini'
#QCLOUDCONFIGFILE = os.getcwd() + '/qcloud-config.ini'
#RESULT = os.getcwd() + '/alertcloud.log'

curr_dir = os.path.dirname(os.path.realpath(__file__))
ALIYUNCONFIGFILE = curr_dir + os.sep + "aliyun-config.ini"
QCLOUDCONFIGFILE = curr_dir + os.sep + "qcloud-config.ini"
RESULT = curr_dir + os.sep + 'alertcloud.log'

today = datetime.datetime.now().strftime('%Y-%m-%d')
todayStr = today.split('-')
expired_dn = datetime.datetime(int(todayStr[0]), int(todayStr[1]), int(todayStr[2]))

from_addr = 'mike@test.com'
to_addr = ['luwen@test.com']
password = '123456'
smtpServer = 'smtp.test.com'

if os.path.exists(RESULT):
    os.remove(RESULT)
f = open(RESULT,'a')


def aliyun_renew_monitor(SecretId,SecretKey,RegionId,InstanceId):

    clt = client.AcsClient(SecretId,SecretKey,RegionId)
    # 设置参数
    request = DescribeInstanceAutoRenewAttributeRequest.DescribeInstanceAutoRenewAttributeRequest()
    request.set_accept_format('json')
    request.add_query_param('InstanceId', InstanceId)
    request.add_query_param('RegionId', RegionId)

    # 发起请求
    response = clt.do_action(request)
    str_response = json.loads(response)
    #return str_response
    return str_response['InstanceRenewAttributes']['InstanceRenewAttribute'][0]

def aliyun_renew_rds_info(SecretId,SecretKey,RegionId,DBInstanceId):

    clt = client.AcsClient(SecretId,SecretKey,RegionId)
    # 设置参数
    request = DescribeInstanceAutoRenewalAttributeRequest.DescribeInstanceAutoRenewalAttributeRequest()
    request.set_accept_format('json')
    request.add_query_param('Action', 'DescribeInstanceAutoRenewalAttribute')
    request.add_query_param('DBInstanceId', DBInstanceId)

    # 发起请求
    response = clt.do_action_with_exception(request)
    str_response = json.loads(response)
    #return str_response
    return str_response


def utc2local(utc_st):
    UTC_FORMAT = "%Y-%m-%dT%H:%MZ"
    UTC2_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    try:
        expired_utc = datetime.datetime.strptime(utc_st, UTC_FORMAT)
    except:
        expired_utc = datetime.datetime.strptime(utc_st, UTC2_FORMAT)
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
            #ecs
            for inst in AliEcs(SecretId,SecretKey,RegionId).aliyun_ecs():
                if inst['InstanceChargeType'] == 'PrePaid':
                    lanIp_aliyun = '-'.join(inst['VpcAttributes']['PrivateIpAddress']['IpAddress'])
                    InstanceId_aliyun = inst['InstanceId']
                    expired_aliyun_time = utc2local(inst['ExpiredTime'])
                    expiredStr_aliyun = expired_aliyun_time.split('-')
                    expired_dw_aliyun = datetime.datetime(int(expiredStr_aliyun[0]),
                            int(expiredStr_aliyun[1]), int(expiredStr_aliyun[2]))
                    periodTime_aliyun = (expired_dw_aliyun - expired_dn).days
                    if periodTime_aliyun <= 7 and periodTime_aliyun >= -3:
                        if inst['Status'] != 'Stopped':
                            AutoRenew_status = aliyun_renew_monitor(SecretId,
                                    SecretKey,RegionId,InstanceId_aliyun)
                            AutoRenew_aliyun = AutoRenew_status['AutoRenewEnabled']
                            if AutoRenew_aliyun:
                                f.write("阿里云%s账号下服务器%s-%s还有%s天过期，此实例自动续费，请密切关注\n"
                                        %(UserName,InstanceId_aliyun,lanIp_aliyun,periodTime_aliyun))
                            else:
                                f.write("阿里云%s账号下服务器%s-%s还有%s天过期，此实例未设置自动续费，请注意续费\n"
                                        %(UserName,InstanceId_aliyun,lanIp_aliyun,periodTime_aliyun))
                        else:
                                f.write("阿里云%s账号下服务器%s-%s还有%s天过期，此实例处于过期回收中，请确认是否续费\n"
                                        %(UserName,InstanceId_aliyun,lanIp_aliyun,periodTime_aliyun))
            #rds
            try:
                result_rds = AliRds(SecretId,SecretKey,RegionId).aliyun_rds()['Items']['DBInstance']
                for inst_rds in result_rds:
                    if inst_rds['PayType'] == 'Prepaid':
                        InstanceId_rds = inst_rds['DBInstanceId']
                        expired_rds_time = utc2local(inst_rds['ExpireTime'])
                        expiredStr_rds = expired_rds_time.split('-')
                        expired_dw_rds = datetime.datetime(int(expiredStr_rds[0]),
                            int(expiredStr_rds[1]), int(expiredStr_rds[2]))
                        periodTime_rds = (expired_dw_rds - expired_dn).days
                        if periodTime_rds <= 1000 and periodTime_rds >= -3:
                            AutoRenew_rds = aliyun_renew_rds_info(SecretId,SecretKey,RegionId,InstanceId_rds)
                            try:
                                AutoRenew_rds = aliyun_renew_rds_info(SecretId,SecretKey,RegionId,InstanceId_rds)['Items']['AutoRenew']
                                if AutoRenew_rds:
                                    f.write("阿里云%s账号下数据库%s还有%s天过期，此实例设置了自动续费，请密切关注\n"
                                            %(UserName,InstanceId_rds,periodTime_rds))
                                else:
                                    f.write("阿里云%s账号下数据库%s还有%s天过期，此实例未设置自动续费，请注意及时续费\n"
                                            %(UserName,InstanceId_rds,periodTime_rds))
                            except:
                                f.write("阿里云%s账号下数据库%s还有%s天过期，此实例未设置自动续费，请注意及时续费\n"
                                        %(UserName,InstanceId_rds,periodTime_rds))


            except:
                pass
            #    print r

    #qcloud
    cfg = ConfigParser()
    cfg.read(QCLOUDCONFIGFILE)
    for account in cfg.sections():
        UserName = str(cfg.get(account,"UserName"))
        SecretId = str(cfg.get(account,"SecretId"))
        SecretKey = str(cfg.get(account,"SecretKey"))
        Regions = str(cfg.get(account,"Region")).split(",")
        for Region in Regions:
            for cvm in QcloudCvm(SecretId,SecretKey,Region).qcloud_ecs():
                InstanceId_qcloud = cvm['instanceId']
                lanIp_qcloud = cvm['lanIp']
                expired_qcloud_time = time2day(cvm['deadlineTime'])
                expiredStr_qcloud = expired_qcloud_time.split('-')
                expired_dw_qcloud = datetime.datetime(int(expiredStr_qcloud[0]),
                        int(expiredStr_qcloud[1]), int(expiredStr_qcloud[2]))
                periodTime_qcloud = (expired_dw_qcloud - expired_dn).days
                if periodTime_qcloud <= 7 and periodTime_aliyun >= -3:
                    if cvm['autoRenew'] == 1:
                        f.write("腾讯云%s账号下服务器%s-%s还有%s天过期，此实例自动续费，请密切关注\n"
                                %(UserName,InstanceId_qcloud,lanIp_qcloud,periodTime_qcloud))
                    else:
                        f.write("腾讯云%s账号下服务器%s-%s还有%s天过期，此实例未设置自动续费，请注意续费\n"
                                %(UserName,InstanceId_qcloud,lanIp_qcloud,periodTime_qcloud))
            for cdb in QcloudCdb(SecretId,SecretKey,Region).qcloud_cdb()['cdbInstanceSet']:
                InstanceId_cdb = cdb['uInstanceId']
                lanIp_cdb = cdb['cdbInstanceVip']
                expired_cdb_time = time2day(cdb['cdbInstanceDeadlineTime'])
                expiredStr_cdb = expired_cdb_time.split('-')
                expired_dw_cdb = datetime.datetime(int(expiredStr_cdb[0]),
                        int(expiredStr_cdb[1]), int(expiredStr_cdb[2]))
                periodTime_cdb = (expired_dw_cdb - expired_dn).days
                if periodTime_qcloud <= 7 and periodTime_aliyun >= -3:
                    if cdb['autoRenew'] == 1:
                        f.write("腾讯云%s账号下数据库%s-%s还有%s天过期，此实例自动续费，请密切关注\n"
                                %(UserName,InstanceId_cdb,lanIp_cdb,periodTime_cdb))
                    else:
                        f.write("腾讯云%s账号下数据库%s-%s还有%s天过期，此实例未设置自动续费，请注意续费\n"
                                %(UserName,InstanceId_cdb,lanIp_cdb,periodTime_cdb))

    f.close()
    #sendmail
    if os.path.getsize(RESULT):
        subject = "云服务器即将过期服务器列表邮件"
        filecon = open(RESULT,"rb")
        content = filecon.read()
        try:
            sendmail(from_addr,password,to_addr,smtpServer,subject,content)
        except Exception, e:
            print 'str(Exception):\t', str(Exception)
            print 'str(e):\t\t', str(e)
        filecon.close()
    else:
        print "没有云主机快过期"
        pass
