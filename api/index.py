from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
        <head>
            <title>A-Share AI Advisor</title>
            <style>
                body { background-color: #0a0908; color: #e5c158; font-family: sans-serif; text-align: center; padding-top: 100px; }
                h1 { letter-spacing: 2px; }
                p { color: #d4c4a8; line-height: 1.6; }
                a { color: #f0c354; text-decoration: none; border-bottom: 1px dashed; }
            </style>
        </head>
        <body>
            <h1>🚀 A 股 AI 量化分析顾问</h1>
            <p>Vercel 部署已就绪。</p>
            <p><strong>注意：</strong>由于 Vercel Serverless Functions 的底层网络限制（不支持 WebSocket 长连接），<br>且云函数最大执行时间限制为 10~60 秒，完整的 Streamlit AI 分析大屏无法在此完美运行。</p>
            <p>为了获得最佳体验（支持长达 2 分钟的投研推演流程与实时交互），<br>强力建议您参考下方仓库，使用本地部署或 Render、Zeabur 等平台。</p>
            <br>
            <p>🔗 <a href="https://github.com/jeffersoninsz/a-share-advisor" target="_blank">前往 GitHub 获取完整部署指南</a></p>
        </body>
    </html>
    """
