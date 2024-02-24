# Zephyr
## 2023雷达站说明文档
### 1. 安装
* STEP1: 在 [此仓库](https://github.com/Gallifreey/Zephyr.git) 中下载Release代码，并解压到合适的文件夹下。或使用git进行拉取 `git clone https://github.com/Gallifreey/Zephyr.git` 。
* STEP2: 安装Node.js环境，在 [Node.js官网](https://nodejs.org/en) 选择较新版本安装，并配置好环境变量，检查Node.js版本是否正确：在cmd中输入`node -v`查看版本，如我的版本为`v16.20.1`。
* STEP3: 进入项目的backend文件夹下进行后端的依赖安装。使用`pip`指令，`pip install -r requirement.txt`。
* STEP4: 进入项目的frontend文件夹下进行前端的依赖安装。使用`npm`指令，`npm install`会自动下载所有依赖。
### 2. 配置
* STEP1: 后端的配置文件在`backend\resource\assets\data`下，具体配置文件格式见[设计文档](DETAIL.md)。
* STEP2: 配置摄像头，本项目暂时仅支持免驱USB摄像头和ZED，若想创建自己的摄像头请见[设计文档](DETAIL.md)。
* STEP3: 配置雷达，本项目暂时仅支持Livox系列的(Mid70、Mid40、Horizon、Tele-15和Hub)，若想使用自己的雷达，请见[设计文档](DETAIL.md)。
* STEP4: 配置前端websocket通讯IP，请修改`src\utils\socket.js`中的ip为后端获得的本机IP，可以在系统WIFI设置中查看自己的IP地址。
### 3. 使用
本项目是前后端分离开发，前端负责显示调试界面，后端负责功能实现。运行前后端时没有前后顺序，若后端启动但前端没有显示请刷新页面。
* STEP1: 启动后端，运行`backend\main.py`。
* STEP2: 启动前端，在`frontend`文件夹下，使用cmd或者IDE运行`npm run serve`。
