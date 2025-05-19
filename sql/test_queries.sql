-- 1. 檢查 symbols 表格是否存在並列出全部內容
SELECT * FROM symbols;

-- 2. 檢查 price_data 表格是否存在並列出前 10 筆資料
SELECT * FROM price_data ORDER BY date DESC LIMIT 10;

-- 3. 查詢某個 symbol 的所有資料（範例：'AAPL'）
SELECT * FROM price_data WHERE symbol = 'AAPL' ORDER BY date;

-- 4. 查詢特定日期範圍的價格（範例：0050.TW 在 2024 年的資料）
SELECT * FROM price_data 
WHERE symbol = '0050.TW' AND date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY date;

-- 5. 查詢某個 symbol 的最大日期（最新資料日期）
SELECT MAX(date) FROM price_data WHERE symbol = 'AAPL';

-- 6. 檢查有多少筆資料（筆數統計）
SELECT symbol, COUNT(*) AS record_count FROM price_data GROUP BY symbol ORDER BY record_count DESC;

-- 7. 查詢資料缺漏情況（例如是否有日期跳空）
-- 這是概念查詢，需搭配 Python 檢查完整日期序列更準確

-- 8. 檢查是否有重複的 symbol/date 組合
SELECT symbol, date, COUNT(*) as count
FROM price_data
GROUP BY symbol, date
HAVING count > 1;

-- 9. 檢查是否有 NULL 值
SELECT * FROM price_data
WHERE open IS NULL OR high IS NULL OR low IS NULL OR close IS NULL OR volume IS NULL;

-- 10. 顯示所有 symbol 最新的一筆收盤價
SELECT symbol, date, close
FROM price_data
WHERE (symbol, date) IN (
    SELECT symbol, MAX(date)
    FROM price_data
    GROUP BY symbol
);
