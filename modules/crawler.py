# crawler.py
# 預留檔案，用於將來自訂資料抓取，例如台股匯率等非 yfinance 資料來源

# 可包含：
# - requests / BeautifulSoup 解析網站
# - API 抓取
# - 專屬轉換格式成 DataFrame

# 範例框架：
# import requests
# import pandas as pd
#
# def fetch_custom_data():
#     response = requests.get("https://example.com/data")
#     data = response.json()
#     df = pd.DataFrame(data)
#     return df
