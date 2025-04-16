# 项目运行与说明
## 配置Reapy库
Reaper可以通过官方提供的ReaScript脚本库，进行各种操作，ReaScript支持EEL2、Lua与Python等语言。
Reapy是将ReaScript Python再次进行封装的Python库，并通过HTTP端口，可以从Reaper外部进行脚本调用。
**配置Reapy库，详细操作也可以参考Reapy库中的详细安装手册部分**
1. 安装Reaper和Python
2. 在Reaper的Preference中，找到ReaScript选项，配置Python信息，并启用Python：“Enable Pthon for use with ReaScript"
![在Reaper中启用Python支持](/article/reaper_python_setting.png)  
3. 在Reaper的Preference中，找到Control/OSC/web选项，配置web信息，端口号为2307
![在Reaper中启用Reapy监听端口](/article/reaper_reapy_server_setting.png)
4. pip install python-reapy 添加Reapy库，这个库可以通过HTTP为媒介，从外部调用Reaper脚本ReaScript
5. 在Reaper的Action中，选择Load-Action，并从Reapy库中选择activate_reapy_server.py文件，运行改脚本启动Reapy在Reaper中的Server
![在Reaper中启用Reapy服务器](/article/reapy_reaper_server.png)

## 配置MCP库
MCP的目标是让大模型可以通过开发者写的工具中间件，调用市面上已存在的各种API结构。
MCP Host就是用户使用的LLM大模型，并且可以运行MCP Client。
MCP Client会分析用户对话，并选择合适的工具中间件（MCP Server）进行调用，并将结果返回给用户
每一个小工具中间件可以对应一个MCP Server，MCP Server有多种运行方式，但本质上都是像Client进行注册
**配置MCP环境**
1. 按照MCP官方指导，安装uv Python虚拟环境，并创建第一个MCP Server来完成配置
2. 本文使用的MCP Host是VS Code with Copliot
3. 在VS Code Setting中选择MCP标签，将MCP配置信息复制到settings.json文件中
**MCP Server 配置信息**
"mcp": {
        "inputs": [],
        "servers": {
            "pxqmr": {
                "command": "uv",
                "args": [
                    "--directory",
                    "C:\\Users\\PXQ\\Desktop\\mcpreaper\\pxqmr", **这里替换成你的运行位置**
                    "run",
                    "main.py"
                ]
            }
        }
    }
4. 打开Copilot，选择Agent模式，就会看到加载了两个MCP工具。
![Copilot](/article/agent_mode.png)
![MCP工具列表](/article/mcp_tools.png)

# 在运行前，务必替换pxqmr/main.py和resource/description.txt中的绝对地址内容

## 文件夹说明
article: 文档中使用的图片
pxqmr: MCP Server本体，main.py是MCP Tools的实现代码
resource：测试用音频，a-g都是同样的声音
testpy: 开发过程中的一些实验代码，Jupyter Notebook中是Reapy的测试代码

## 运行示例
![运行示例](/article/full_processing.png)
![导入效果](/article/after_import.png)
