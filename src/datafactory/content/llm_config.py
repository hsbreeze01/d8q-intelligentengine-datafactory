"""LLM内容创作配置 - 支持多 provider 切换"""
import json
import os

# 配置文件路径
PROVIDERS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "llm_providers.json")
CONTENT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "llm_content_config.json")

# 默认 provider 配置
DEFAULT_PROVIDERS = {
    "active": "qwen",
    "providers": {
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "api_key": "",
            "model": "deepseek-chat",
            "request_timeout_s": 60,
            "max_requests_per_minute": 60,
            "max_retries": 3,
            "extra_body": {}
        },
        "qwen": {
            "base_url": "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
            "api_key": "",
            "model": "qwen3.7-plus",
            "request_timeout_s": 120,
            "max_requests_per_minute": 60,
            "max_retries": 3,
            "extra_body": {}
        }
    }
}

# 默认内容创作配置
DEFAULT_CONTENT = {
    "news_brief": {
        "name": "资讯速递",
        "max_items": 5,
        "title_prompt": "你是小红书爆款标题专家。根据以下资讯列表，生成一个吸引眼球的标题。要求：带emoji，不超过20字，有悬念感。只输出标题，不要其他内容。",
        "content_prompt": "你是小红书内容创作专家。根据以下资讯，创作一篇小红书风格的资讯速递。要求：\n1. 从中筛选最有价值的{max_items}条，去除重复\n2. 每条用1-2句话精炼概括，前面加数字emoji（1️⃣2️⃣3️⃣）\n3. 语气轻松专业，适合年轻读者\n4. 总字数控制在300-500字\n5. 末尾空一行后加话题标签\n6. 不要加标题（标题单独生成）",
        "default_tags": ["#AI资讯", "#科技前沿", "#人工智能"],
        "extra_tags_prompt": "根据以下内容，生成3个最相关的小红书话题标签（格式：#标签），只输出标签，用空格分隔。",
    },
    "research_report": {
        "name": "研究报告",
        "title_prompt": "你是小红书财经博主。根据以下研报和资讯数据，生成一个专业又吸引人的标题。要求：带emoji，不超过20字，体现深度分析感。只输出标题。",
        "content_prompt": "你是资深财经分析师兼小红书博主。根据以下研报数据和行业资讯，创作一篇小红书风格的深度分析文章。要求：\n1. 分三个板块：【本周核心】【机构观点】【关注要点】\n2. 【机构观点】引用具体券商/机构名称和观点，用▪️列表\n3. 【关注要点】用✅标注机会，⚠️标注风险\n4. 语气专业但易懂，适合投资小白\n5. 总字数控制在500-800字\n6. 末尾空一行后加话题标签\n7. 不要加标题",
        "default_tags": ["#投资分析", "#研报解读", "#A股"],
        "extra_tags_prompt": "根据以下内容，生成3个最相关的小红书投资话题标签（格式：#标签），只输出标签，用空格分隔。",
    },
}


def load_providers_config():
    """加载 provider 配置"""
    if os.path.exists(PROVIDERS_CONFIG_PATH):
        try:
            with open(PROVIDERS_CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_PROVIDERS))


def load_content_config():
    """加载内容创作配置"""
    if os.path.exists(CONTENT_CONFIG_PATH):
        try:
            with open(CONTENT_CONFIG_PATH, encoding="utf-8") as f:
                saved = json.load(f)
            merged = json.loads(json.dumps(DEFAULT_CONTENT))
            for k, v in saved.items():
                if isinstance(v, dict) and k in merged:
                    merged[k].update(v)
                else:
                    merged[k] = v
            return merged
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_CONTENT))


def get_active_llm_config():
    """获取当前活跃的 LLM 配置"""
    providers_config = load_providers_config()
    active_provider = providers_config.get("active", "qwen")
    provider = providers_config.get("providers", {}).get(active_provider, {})
    
    return {
        "api_key": provider.get("api_key", ""),
        "base_url": provider.get("base_url", ""),
        "model": provider.get("model", "deepseek-chat"),
        "temperature": 0.7,
        "max_tokens": 2000,
    }


def load_config():
    """加载完整配置（兼容旧接口）"""
    llm_config = get_active_llm_config()
    content_config = load_content_config()
    
    return {
        "llm": llm_config,
        **content_config
    }


def save_config(config):
    """保存配置（兼容旧接口，只保存内容部分）"""
    content = {k: v for k, v in config.items() if k != "llm"}
    os.makedirs(os.path.dirname(CONTENT_CONFIG_PATH), exist_ok=True)
    with open(CONTENT_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
