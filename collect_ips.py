import requests
from bs4 import BeautifulSoup
import re
import os
import logging

# 配置日志
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger("collect_ips")

# 可选：初始化 Sentry（如果提供了 SENTRY_DSN）
SENTRY_DSN = os.getenv("SENTRY_DSN")
sentry_inited = False
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0")),
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        )
        sentry_inited = True
        logger.info("Sentry initialized")
    except Exception as e:
        logger.warning(f"Failed to init Sentry: {e}")

# 目标URL列表
urls = [
    'https://api.uouin.com/cloudflare.html',
    'https://ip.164746.xyz'
]

# 正则表达式用于匹配IP地址
ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'

def main():
    # 检查ip.txt文件是否存在,如果存在则删除它
    if os.path.exists('ip.txt'):
        os.remove('ip.txt')

    # 创建一个文件来存储IP地址
    with open('ip.txt', 'w') as file:
        for url in urls:
            logger.info(f"Fetching {url}")
            # 发送HTTP请求获取网页内容
            response = requests.get(url, timeout=20)

            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 根据网站的不同结构找到包含IP地址的元素
            if url == 'https://api.uouin.com/cloudflare.html':
                elements = soup.find_all('tr')
            elif url == 'https://ip.164746.xyz':
                elements = soup.find_all('tr')
            else:
                elements = soup.find_all('li')

            # 遍历所有元素,查找IP地址
            count = 0
            for element in elements:
                element_text = element.get_text()
                ip_matches = re.findall(ip_pattern, element_text)

                # 如果找到IP地址,则写入文件
                for ip in ip_matches:
                    file.write(ip + '\n')
                    count += 1
            logger.info(f"Extracted approximately {count} ips from {url}")

    logger.info('IP地址已保存到ip.txt文件中。')


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
            logger.exception("任务失败")
            if SENTRY_DSN:
                try:
                    import sentry_sdk  # may or may not exist
                    sentry_sdk.capture_exception(e)
                except Exception:
                    pass
            raise
