# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import os
import random
import time
import sys
import io
import json
import time
import datetime
from azure.storage.blob import BlockBlobService, PublicAccess

# Imports for the REST API
from flask import Flask, request

import iothub_client
# pylint: disable=E0611
from iothub_client import IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0

# Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
PROTOCOL = IoTHubTransportProvider.MQTT

app = Flask(__name__)

# 4MB Max image size limit
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 

# Blob Upload Setting 
BLOB_UPLOAD_DURATION_SEC = 10 
IMAGE_CONTAINER_NAME = "edgephotos"
blobLastUploadTime = time.time()

blobService = None
storeImageRequestCount = 0

# Default route just shows simple text
@app.route('/')
def index():
    return 'store image to blob on edge harness'

# Like the CustomVision.ai Prediction service /image route handles either
#     - octet-stream image file 
#     - a multipart/form-data with files in the imageData parameter
@app.route('/image', methods=['POST'])
def store_image_handler():
    global storeImageRequestCount
    global blobService
    try:
        storeImageRequestCount += 1
        if ((storeImageRequestCount%10) ==0):
            print("images received - " + str(storeImageRequestCount))
            imageData = None
            if ('imageData' in request.files):
                imageData = request.files['imageData']
            else:
                imageData = io.BytesIO(request.get_data())
                blobService.upload_image_to_blob(imageData)
                print('stored image')
        results = []
        return json.dumps(results)
    except Exception as e:
        print('EXCEPTION:', str(e))
        return 'Error processing image', 500

class BlobService(object):
    def __init__(
            self,
            blobonedge_module_name,
            blob_account_name,
            blob_account_key,
            image_container_name,
            image_upload_duration_sec,
            edge_id
        ):
        localblob_connectionstring = 'DefaultEndpointsProtocol=http;BlobEndpoint=http://'+blobonedge_module_name+':11002/'+blob_account_name+';AccountName='+blob_account_name+';AccountKey='+blob_account_key+';'
        print("Try to connect to blob on edge by "+localblob_connectionstring)
        self.blockBlobService = BlockBlobService(endpoint_suffix='', connection_string=localblob_connectionstring)
        print("Connected to blob on edge")
        self.blockBlobService.create_container(image_container_name)
        print('Created image container - '+image_container_name)
        self.imageContainerName = image_container_name
        self.imageUploadDurationSec = image_upload_duration_sec
        self.edgeId = edge_id
        self.blobLastUploadTime = time.time()

    def upload_image_to_blob(self, image):
        now = datetime.datetime.now()
        currentTime = time.time()
        print('Last Time:'+str(self.blobLastUploadTime)+'->Current:'+str(currentTime))
        if (currentTime - self.blobLastUploadTime > self.imageUploadDurationSec):
            image_file_name = self.edgeId + "-img{0:%Y%m%d%H%M%S}".format(now) +".jpg"
            # image_file_name = "image{0:%Y%m%d%H%M%S}".format(now) +".jpg"
            print('Uploading image as '+image_file_name + ' at ' + str(currentTime))
            self.blockBlobService.create_blob_from_stream(self.imageContainerName, image_file_name, image)
            print('Upload done')
            self.blobLastUploadTime = currentTime


def main(protocol):
    try:
        print ( "\nPython %s\n" % sys.version )

    except KeyboardInterrupt:
        print ( "IoTHubModuleClient sample stopped" )

def initialize_blob_on_edge(blobOnEdgeModule,blobOnEdgeAccountName,blobOnEdgeAccountKey,imageContainerName, blobUploadDurationSec, edgeId):
    blobService = BlobService(blobOnEdgeModule, blobOnEdgeAccountName, blobOnEdgeAccountKey,imageContainerName,blobUploadDurationSec, edgeId)
    return blobService

if __name__ == '__main__':
    print('version : 0.3.0')
    print('app is '+__name__)
    # main(PROTOCOL)
    # for key in os.environ.keys():
    #    print('key='+key+":value="+os.environ[key])

    BLOB_ON_EDGE_MODULE = os.environ['BLOB_ON_EDGE_MODULE']
    BLOB_ON_EDGE_ACCOUNT_NAME = os.environ['BLOB_ON_EDGE_ACCOUNT_NAME']
    BLOB_ON_EDGE_ACCOUNT_KEY = os.environ['BLOB_ON_EDGE_ACCOUNT_KEY']
    IMAGE_CONTAINER_NAME=os.environ['IMAGE_CONTAINER_NAME']
    IOTEDGE_DEVICEID=os.environ['IOTEDGE_DEVICEID']
    BLOB_UPLOAD_DURATION_SEC = float(os.environ["BLOB_UPLOAD_DURATION_SEC"])
    

    print('IOTEDGE_DEVICEID:'+ IOTEDGE_DEVICEID)
    print('BLOB_ON_EDGE_MODULE:'+BLOB_ON_EDGE_MODULE)
    print('BLOB_ON_EDGE_ACCOUNT_NAME:'+BLOB_ON_EDGE_ACCOUNT_NAME)
    print('BLOB_ON_EDGE_ACCOUNT_KEY:'+BLOB_ON_EDGE_ACCOUNT_KEY)
    print('IMAGE_CONTAINER_NAME:'+IMAGE_CONTAINER_NAME)
    print('BLOB_UPLOAD_DURATION_SEC='+str(BLOB_UPLOAD_DURATION_SEC))

    blobService = initialize_blob_on_edge(BLOB_ON_EDGE_MODULE,BLOB_ON_EDGE_ACCOUNT_NAME,BLOB_ON_EDGE_ACCOUNT_KEY,IMAGE_CONTAINER_NAME,BLOB_UPLOAD_DURATION_SEC,IOTEDGE_DEVICEID)

    app.run(host='0.0.0.0', port=80, debug=True)
