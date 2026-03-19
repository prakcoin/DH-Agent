from strands import tool
from tavily import TavilyClient
import logging
import os

log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
logging.basicConfig(format="[%(asctime)s] %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

AWS_REGION = os.getenv("AWS_REGION")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    
@tool
def web_crawl(query: str) -> str:
    """
    Perform a web crawl for information.

    Use this tool when deeper research is required, such as collection history, runway analysis, design inspirations, or editorial commentary.

    Args:
    query (str): A search query for Tavily crawl.

    Returns:
    Raw JSON search results. 
    Return "Research failed." if the request is unsuccessful.
    """
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

    try:
        response = tavily_client.crawl(
            url="https://www.grailed.com/designers/dior",
            instructions=f"Find listings based on the query: {query}",
            extract_depth="advanced",
            select_paths=[".*listings.*"], 
            # exclude_paths=[
            #     "/about.*", 
            #     "/help.*", 
            #     "/cart.*", 
            #     "/login.*", 
            #     "/terms.*",
            #     "/messages.*"
            # ],    
            max_depth=1,
            max_breadth=100,
            limit=100
        )
        results = response.get("results", [])
        
        if not results:
            return "No specific archival data found for this query."

        formatted_results = []
        for item in results:
            content = item.get("raw_content", "")
            url = item.get("url", "")
            
            formatted_results.append(f"SOURCE: {url}\nCONTENT: {content[:2000]}...")

        return "\n\n---\n\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Tavily request failed: {e}")
        return "Research failed."