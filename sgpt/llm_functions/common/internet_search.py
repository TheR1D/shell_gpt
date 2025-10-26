import requests
from bs4 import BeautifulSoup
import time
from typing import List, Tuple
import os

SEARCH_CONFIG = {
    "INTERNET_SEARCH_ENGINE_API": os.getenv("INTERNET_SEARCH_ENGINE_API", "https://www.googleapis.com/customsearch/v1"),
    "INTERNET_SEARCH_API_KEY": os.getenv("INTERNET_SEARCH_API_KEY", None),
    "INTERNET_SEARCH_API_CX": os.getenv("INTERNET_SEARCH_API_CX", None)
}

def googleapis(query, num) -> List[Tuple[str, str]]:
    """
    使用Google Custom Search API进行搜索
    
    Args:
        query: 搜索关键词
        num: 返回结果数量
        
    Returns:
        list[tuple[str, str]]: [(标题, 链接), ...]
        
    Raises:
        ValueError: 当API密钥或CX未配置时
        requests.exceptions.RequestException: 网络请求异常
        KeyError: API返回数据格式异常
    """
    # 检查必要配置
    if not SEARCH_CONFIG["INTERNET_SEARCH_API_KEY"]:
        raise ValueError("Google Search API key is not configured")
    
    if not SEARCH_CONFIG["INTERNET_SEARCH_API_CX"]:
        raise ValueError("Google Search API CX is not configured")
    
    url = SEARCH_CONFIG["INTERNET_SEARCH_ENGINE_API"]
    params = {
        "q": query,
        "num": num,
        "safe": "off",
        "key": SEARCH_CONFIG["INTERNET_SEARCH_API_KEY"],
        "cx": SEARCH_CONFIG["INTERNET_SEARCH_API_CX"],
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 检查API是否返回错误
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown API error")
            raise requests.exceptions.RequestException(f"Google API error: {error_msg}")
        
        results = []
        items = data.get("items", [])
        
        for item in items:
            title = item.get("title", "")
            link = item.get("link", "")
            if title and link:
                results.append((title, link))
        
        return results
        
    except requests.exceptions.Timeout:
        raise requests.exceptions.Timeout("Google Search API request timeout")
    except requests.exceptions.RequestException:
        raise
    except ValueError as e:
        # JSON解析错误
        raise requests.exceptions.RequestException(f"Failed to parse API response: {str(e)}")

def fetch_and_process_web_content(search_results: list) -> List[Tuple[str, str]]:
    """
    顺次访问搜索结果中的URL，获取网页内容并清洗处理
    
    Args:
        search_results: 由googleapis函数返回的[(title, url), ...]列表
        
    Returns:
        list[tuple[str, str]]: [(标题, 清洗后的内容), ...]
    """
    processed_content = []
    
    for title, url in search_results:
        try:
            # 添加延时避免请求过快
            # time.sleep(0.5)
            
            # 设置请求头模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 尝试获取主要内容区域
            # 优先查找内容相关的标签
            content_selectors = [
                'main', 'article', '[role="main"]', '.content', '#content',
                '.post', '.article', 'body'
            ]
            
            text_content = ""
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    text_content = content_element.get_text(separator=' ', strip=True)
                    break
            
            if not text_content:
                # 如果没找到特定内容区域，获取整个body的文本
                body = soup.find('body')
                if body:
                    text_content = body.get_text(separator=' ', strip=True)
                else:
                    text_content = soup.get_text(separator=' ', strip=True)
            
            # 清洗文本内容
            # 移除多余的空白字符和换行符
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = ' '.join(chunk for chunk in chunks if chunk)
            
            # 限制内容长度以避免过长
            if len(text_content) > 4096:
                text_content = text_content[:4096] + "..."
            
            processed_content.append((title, text_content))
            
        except Exception as e:
            # 如果获取网页失败，添加错误信息
            processed_content.append((title, f"Faild to fetch content: {str(e)}"))
    
    return processed_content

def convert_to_readable_string(processed_content: List[Tuple[str, str]]) -> str:
    """
    将处理后的内容转换为可读的长字符串
    
    Args:
        processed_content: [(标题, 内容), ...]列表
        
    Returns:
        str: 格式化的长字符串
    """
    result_parts = []
    
    for i, (title, content) in enumerate(processed_content, 1):
        section = f"=== No.{i} result ===\n"
        section += f"Title: {title}\n"
        section += f"Content: {content}\n"
        section += "=" * 50 + "\n"
        result_parts.append(section)
    
    return "\n".join(result_parts)

# 使用示例:
# search_results = googleapis("hello", 5)
# processed_content = fetch_and_process_web_content(search_results)
# readable_string = convert_to_readable_string(processed_content)