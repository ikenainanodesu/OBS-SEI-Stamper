# 我没有任何vs基础，请从0开始一步一步教我。
# 生成的文档与回答请全部使用中文
# 我想为obs开发一个插件
    - 假设发送端和接收端使用同一ntp服务器
        - 功能是对多个srt源进行基于同一ntp服务器的帧同步
            - 尽量做到传输与渲染的帧同步(保证在obs上看到来自同一源的同一画面与声音维持帧同步)
        - 需要可以兼容使用sls服务器
        - 需要支持intel quicksync硬件解码
        - 需要支持nvidia hardware decode
        - 需要支持AMD hardware decode
        - UI
            - 要求有和原生obs一样的选项
            - 额外要求有ntp服务器地址输入框