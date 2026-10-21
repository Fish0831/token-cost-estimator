from rich.console import Console

MAX_WIDTH = 100  # 外框最寬 100 個字元寬，避免在寬螢幕上被拉得太扁

console = Console(width=min(Console().width, MAX_WIDTH))


def shorten(text: str, limit: int = 120) -> str:
    """太長的文字只顯示前 limit 個字，後面用……代替。只影響畫面顯示。"""
    return text if len(text) <= limit else text[:limit] + "……"
