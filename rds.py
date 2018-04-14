#!/usr/bin/env python
#coding=utf-8
import json
from aliyunsdkcore import client
from aliyunsdkrds.request.v20140815 import DescribeDBInstancesRequest
from QcloudApi.qcloudapi import QcloudApi
class AliRds(object):
    def __init__(self,SecretId,SecretKey,RegionId):
        self.SecretId = SecretId
        self.SecretKey = SecretKey
        self.RegionId = RegionId

    def aliyun_rds(self):
        clt = client.AcsClient(self.SecretId,self.SecretKey,self.RegionId)
        # 设置参数
        request = DescribeDBInstancesRequest.DescribeDBInstancesRequest()
        request.set_accept_format('json')
        request.add_query_param('PageNumber', 1)
        request.add_query_param('PageSize', 100)
        # 发起请求
        request.add_query_param('RegionId', self.RegionId)
        response = clt.do_action(request)
        str_response = json.loads(response)
        return str_response
class QcloudCdb(object):
    def __init__(self,SecretId,SecretKey,Region):
        self.SecretId = SecretId
        self.SecretKey = SecretKey
        self.Region = Region

    def qcloud_cdb(self):
        module = 'cdb'
        action = 'DescribeCdbInstances'
        action_params = {
            'limit':100,
        }
        config = {
            'Region': self.Region,
            'secretId': self.SecretId,
            'secretKey': self.SecretKey,
        }

        try:
            service = QcloudApi(module, config)
            response = json.loads(service.call(action, action_params))
            return response
        except Exception as e:
            import traceback
            print('traceback.format_exc():\n%s' % traceback.format_exc())

if __name__ == '__main__':
    obj = AliRds('***********8','*********************8','cn-hangzhou')
    res = obj.aliyun_rds()
    for i in res['Items']['DBInstance']:
        print i
    qobj = QcloudCdb('*********************88','**********************','ap-beijing')
    qres = qobj.qcloud_cdb()
    #for i in qres['cdbInstanceSet']:
    #    print i
