#!/usr/bin/env python
# encoding: utf-8
import json
from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526 import DescribeInstanceAutoRenewAttributeRequest
from QcloudApi.qcloudapi import QcloudApi

class AliEcs(object):
    def __init__(self,SecretId,SecretKey,RegionId):
        self.SecretId = SecretId
        self.SecretKey = SecretKey
        self.RegionId = RegionId
    def aliyun_ecs(self):
        #ecs_list = []
        clt = client.AcsClient(self.SecretId,self.SecretKey,self.RegionId)

        # 设置参数
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_accept_format('json')
        request.add_query_param('RegionId', self.RegionId)
        request.add_query_param('PageNumber', 1)
        request.add_query_param('PageSize', 100)

        # 发起请求
        response = clt.do_action(request)
        str_response = json.loads(response)
        return str_response['Instances']['Instance']
        #return str_response


class QcloudCvm(object):
    def __init__(self,SecretId,SecretKey,Region):
        self.SecretId = SecretId
        self.SecretKey = SecretKey
        self.Region = Region
    def qcloud_ecs(self):
        module = 'cvm'
        action = 'DescribeInstances'
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
            #print service.generateUrl(action, action_params)
            inst = json.loads(service.call(action, action_params))
            return inst['instanceSet']
        except Exception as e:
            import traceback
            print('traceback.format_exc():\n%s' % traceback.format_exc())
if __name__ == '__main__':
    #obj = AliEcs('***********88','***************8','cn-hangzhou')
    #res = obj.aliyun_ecs()
    #print res
    obj = QcloudCvm('********************8','*****************','ap-beijing')
    res = obj.qcloud_ecs()
    print res
