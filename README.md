# AzureIoTBlobOnEdgeSample 
Azure IoT Edge で、デバイスに搭載されたカメラで動画をとりこみ、指定された時間間隔で、デバイスローカルの Blob on Edge に画像を格納し、Azure 上の Blob Containerに画像をアップロードする。 
![overview](images/overview.png) 
camera-capture は、[https://github.com/ms-iotkithol-jp/Custom-vision-service-iot-edge-raspberry-pi](https://github.com/ms-iotkithol-jp/Custom-vision-service-iot-edge-raspberry-pi) を流用。 
local-blob-storage は、Azure Marketplace から公開されているモジュールを利用。  
store-image-to-local-blob は、このリポジトリの、UploadCameraImageEdgeToCloud/modules/StoreImageToLocalBlob にソースコードと Module Image の Buildが格納されている。 

## 動かし方 
VS Code で UploadCameraImageToCloud を開く  
UploadCameraImageEdgeToCLoud/.env に各自のAzure Container Registry のアクセス情報を設定  
deployment.template.json に各自の設定を追加  
Build & Deploy 
以上！

## 動かない！ 
動かない場合の対処法ですが、まずは、ラズパイのシェル上で以下を実行して全てのモジュールが正常に動いているかを確認する。  
```shell
$ sudo iotedge list
```
正常に動いていないモジュールがあれば、例えば、local-blob-storageなら 
```shell
$ sudo iotedge logs local-blob-storage
```
で、実行ログを表示し原因を探る。  
一番ありがちなのは、Storage Account Name と Storage Account Key（ローカルとクラウド両方あるので注意）の設定が正しくない状況。これは何度も確認してみよう。  
※ [Blob On Edgeの参考情報](https://docs.microsoft.com/ja-jp/azure/iot-edge/how-to-deploy-blob)  

特に、Blob on Edgeが使う、ラズパイのディレクトリの権限も正しいかどうかチェックしよう。 というか、それっぽいログが表示されていたら、作り直してみるのも一法 
```shell
$ cd /srv
$ sudo rm -fr containerdata
$ sudo mkdir containerdata
$ sudo chown -R 11000:11000 /srv/containerdata 
$ sudo chmod -R 700 /srv/containerdata
```
これやったらたいてい動きます。あ、これやるときには、IoT Edge Runtimeを止めること 
```shell
$ sudo systemctl stop iotedge
```
作業が終わったら  
```shell
$ sudo systemctl start iotedge
```

store-image-to-local-blobのロジックを修正した場合、本来はバージョンやタグをつけなおしてDocker Registry にPushして、deployment.template.jsonのモジュールのimageを変えるべきなんだけど、これやらないと、たとえIoT Edge Runtimeを再起動してもIoT Edge Runtimeは、モジュールが変わったことに気づかないようになっているけど、めんどくさいんで、手っ取り早く試すためには、以下をやってね。まずIoT Edge Runtimeを止めてから 
```
$ sudo docker images 
``` 
で、store-image-to-local-blobのDocker Image Idを表示させて
```
$ sudo docker image rm -f <docker image id> 
``` 
で、現在Pullされている、Docker Image を削除してから、IoT Edge Runtimeを起動する。Imageがラズパイ上にないので、新たにPullしてきてくれて、更新されたロジックが実行されるよ。 

