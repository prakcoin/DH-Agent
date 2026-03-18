from strands import tool
import json
import base64
from urllib.parse import urlparse
import os
import boto3
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import retrieve, image_reader
from src.agents.hooks import LimitToolCounts
from botocore.config import Config as BotocoreConfig

s3 = boto3.client('s3', region_name=os.getenv("AWS_REGION"))
bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_REGION"))
BUCKET_NAME = 'aw04-data'
IMAGE_FOLDER = 'images/'
FOLDER_PREFIX = 'looks/'
CLOUDFRONT_DOMAIN = 'https://d39bzdkvoca64w.cloudfront.net'

bedrock_model = BedrockModel(
    model_id="us.amazon.nova-2-lite-v1:0",
)

def parse_filenames_from_string(filenames_str):
    s = filenames_str.strip().lstrip("[").rstrip("]")
    parts = s.split(",")
    urls = [p.strip().strip('"').strip("'") for p in parts if p.strip()]
    return urls

@tool
def get_look_images(look_number: str):
    """
    Retrieve the runway images for a specific look.
    
    Use this tool when a user asks to see a specific runway look. Only use it when you have a look number.
    
    Args:
    look_number (str): The unique identifier for the look, e.g., "1".

    Returns: 
    A list of image URLs for the look.
    """
    prefix = f"{IMAGE_FOLDER}look{look_number}_"
    
    image_objects = s3.list_objects_v2(
        Bucket=BUCKET_NAME, 
        Prefix=prefix,
    )
    
    image_urls = []
    
    if 'Contents' in image_objects:
        for obj in image_objects['Contents']:
            key = obj['Key']
            if key.lower().endswith(('.jpg', '.jpeg', '.png')):
                full_url = f"{CLOUDFRONT_DOMAIN}/{key}"
                image_urls.append(full_url)
    
    return image_urls

@tool
def get_image_details(image_filenames, query: str):
    """
    Perform grounded visual analysis on one or more look images.

    Use this tool when a query requires direct visual inspection of garments, accessories, layering, closures, construction details, or physical attributes that cannot be reliably inferred from metadata alone. 

    Args:
    image_filenames (list): One or more image filenames or URLs associated with a look.
    query (str): A specific visual question to answer.

    Returns:
    A structured textual analysis based only on confirmed visual observations.
    """
    try:
        if not image_filenames:
            return "Error: No image filenames provided."

        if isinstance(image_filenames, str):
            image_filenames = parse_filenames_from_string(image_filenames)

        content_blocks = []

        for filename in image_filenames:
            parsed = urlparse(filename)
            clean_filename = os.path.basename(parsed.path)
            image_key = f"images/{clean_filename}"

            response = s3.get_object(Bucket=BUCKET_NAME, Key=image_key)
            image_bytes = response['Body'].read()

            content_blocks.append({
                "image": {
                    "format": "jpeg",
                    "source": {
                        "bytes": base64.b64encode(image_bytes).decode("utf-8")
                    }
                }
            })

        content_blocks.append({
            "text": f"""
You are performing grounded visual analysis.

Multiple images of the same look may be provided.
Use all images collectively.
If a detail is visible in only one image, it counts as present.
If images conflict, prefer the clearest view.

STEP 1 — Visual Inventory
List all visible garments and accessories from top to bottom.
For each item include:
- Type
- Basic color (single word)
- Visible construction details
- Position on body
- Any visible hardware
If uncertain, state "unclear due to resolution."

Do not infer brand, season accuracy, or intent.

STEP 2 — Focused Scan
If the query involves:
- Jewelry: scan wrists, fingers, neck specifically.
- Layers: count neckline layers and sleeve layers separately.
- Closure: describe fastening mechanism before naming it.
- Lapels: describe shape before classifying.
- Hem: describe fold, stacking, or raw edge appearance.

STEP 3 — Answer
Answer the query using only confirmed observations.
If evidence is insufficient, state that clearly.

Query: {query}
"""
        })

        body = json.dumps({
            "inferenceConfig": {
                "max_new_tokens": 700,
                "temperature": 0.0
            },
            "messages": [
                {
                    "role": "user",
                    "content": content_blocks
                }
            ]
        })

        response = bedrock.invoke_model(
            modelId="amazon.nova-pro-v1:0",
            body=body
        )

        response_body = json.loads(response.get("body").read())
        return response_body["output"]["message"]["content"][0]["text"]

    except Exception as e:
        return f"Error analyzing images {image_filenames}: {str(e)}"
    
KB_PROMPT = """
Role:
Retrieve the look number, category, subcategory, primary and secondary color(s), pattern, primary and secondary outer material(s), and additional notes from the knowledge base based on the query.

Guidelines: 
If the look number is already included in the query, there is no need to retrieve it from the knowledge base.
Make sure the look number retrieved is a positive integer, and not a word or float. 
If retrieve returns no results or an error, return: INFO_NOT_AVAILABLE.
"""

VISUAL_PROMPT = """
Analyze look images for fit, silhouette, texture, and aesthetic details.

Guidelines:
Use the look number provided from the retrieved results to get the filenames using the get_look_images tool. 
Pass the retrieved image filenames into get_image_details in order to retrieve detailed visual analysis.
If get_look_images returns an empty list or an error, return: IMAGE_NOT_AVAILABLE.
"""

SYNTHESIS_PROMPT = """
Role:
Synthesize a final answer based on visual and knowledge base information.

Guidelines:
Combine visual analysis with metadata for the final answer.
Report discrepancies between visual and metadata observations.
"""

@tool 
def get_visual_confirmation(query: str) -> str:
    """
    Perform visual analysis based on a query, in order to confirm details not present in the knowledge base.

    Use this tool when a query requires direct visual inspection of garments, accessories, layering, closures, construction details, or physical attributes that cannot be reliably inferred from metadata alone. 

    Args:
    query (str): A specific visual question to answer.

    Returns:
    A structured textual analysis based only on confirmed visual observations.
    """
    limit_hook = LimitToolCounts(max_tool_counts={"retrieve": 3})

    kb_agent = Agent(model=bedrock_model,
        system_prompt=KB_PROMPT, tools=[retrieve], hooks=[limit_hook])
    visual_agent = Agent(model=bedrock_model,
        system_prompt=VISUAL_PROMPT, tools=[get_look_images, get_image_details])
    synthesis_agent = Agent(model=bedrock_model,
        system_prompt=SYNTHESIS_PROMPT)

    kb_results = kb_agent(f"Retrieve the look number based on this query: {query}")
    if not str(kb_results).strip():
        return "The retrieval system failed to return a response. Please try again."
    if "info_not_available" in str(kb_results).lower():
        return f"I'm sorry, I couldn't find a specific look in our records for '{query}'."
    visual_results = visual_agent(f"Based on the look number retrieved, answer the query. Retrived results: {str(kb_results)}. Query: {query}.")
    if not str(visual_results).strip():
        return "The visual analysis system failed to return a response. Please try again."
    if "image_not_available" in str(visual_results).lower():
        return f"I found the metadata for '{query}', but no archival images were available for visual analysis."
    response = synthesis_agent(f"Synthesize a final result for this query: {query}. Visual results: {str(visual_results)}. Knowledge base results: {str(kb_results)}.")
    return response

@tool
def image_retrieve(image_path: str) -> str:
    """
    Perform image-retrieval from the image knowledge base.

    Use this tool when a query requires direct visual inspection of garments, accessories, layering, closures, construction details, or physical attributes that cannot be reliably inferred from metadata alone. 

    Args:
    image_path (str): The image to use as a retrieval key.

    Returns:
    A structured textual analysis based only on confirmed visual observations.
    """
    kb_id = os.getenv("IMAGE_KNOWLEDGE_BASE_ID")
    region_name = os.getenv("AWS_REGION")
    min_score = 0.4
    
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = base64.b64encode(image_file.read()).decode("utf-8")

        config = BotocoreConfig(user_agent_extra="archival-research-agent")
        client = boto3.client("bedrock-agent-runtime", region_name=region_name, config=config)

        image_format = image_path.split('.')[-1].lower()
        if image_format == 'jpg':
            image_format = 'jpeg'

        retrieval_query = {
            "type": "IMAGE",
            "image": {
                "format": image_format,
                "inlineContent": base64.b64decode(image_bytes)
            }
        }

        retrieval_config = {
            "vectorSearchConfiguration": {
                "numberOfResults": 3
            }
        }

        response = client.retrieve(
            retrievalQuery=retrieval_query,
            knowledgeBaseId=kb_id,
            retrievalConfiguration=retrieval_config
        )

        all_results = response.get("retrievalResults", [])
        
        filtered_results = [r for r in all_results if r.get("score", 0.0) >= min_score]
        
        if not filtered_results:
            return f"No results found above score threshold of {min_score}."

        formatted = []
        for result in filtered_results:
            location = result.get("location", {})
            
            doc_id = "Unknown"
            if "s3Location" in location:
                doc_id = location["s3Location"].get("uri", "Unknown")
            elif "customDocumentLocation" in location:
                doc_id = location["customDocumentLocation"].get("id", "Unknown")
            
            score = result.get("score", 0.0)
            formatted.append(f"\nScore: {score:.4f}")
            formatted.append(f"Document ID: {doc_id}")

            content = result.get("content", {})
            if content and isinstance(content.get("text"), str):
                formatted.append(f"Content: {content['text']}\n")

        formatted_results_str = "\n".join(formatted)

        return f"Retrieved {len(filtered_results)} results with score >= {min_score}:\n{formatted_results_str}"
    except Exception as e:
        return f"Error during visual retrieval: {str(e)}"

@tool
def get_cloudfront_url(image_filename: str):
    """
    Convert a single archival filename into its corresponding CloudFront URL.
    
    Args:
        image_filename (str): The specific filename (e.g., "look30_1.jpg").

    Returns: 
        str: The full CloudFront URL for that specific image.
    """
    clean_name = image_filename.split('/')[-1].replace('`', '').strip()
    full_url = f"{CLOUDFRONT_DOMAIN}/{IMAGE_FOLDER}{clean_name}"
    
    return full_url

@tool
def get_image_comparison(query_filename: str, retrieved_filename: str):
    """
    Perform a direct side-by-side visual comparison between a query image and a single archival look image.

    Args:
        query_filename (str): Local path to the user's query image.
        retrieved_filename (str): The filename or URL of the archival image.

    Returns:
        A analysis and comparison of the images.
    """
    try:
        content_blocks = []

        with open(query_filename, "rb") as f:
            query_bytes = f.read()
        
        content_blocks.append({"text": "IMAGE A (Query):"})
        content_blocks.append({
            "image": {
                "format": "jpeg",
                "source": {"bytes": base64.b64encode(query_bytes).decode("utf-8")}
            }
        })

        clean_retrieved = os.path.basename(urlparse(retrieved_filename).path)
        image_key = f"{IMAGE_FOLDER}{clean_retrieved}"

        response = s3.get_object(Bucket=BUCKET_NAME, Key=image_key)
        retrieved_bytes = response['Body'].read()

        content_blocks.append({"text": "IMAGE B (Retrieved):"})
        content_blocks.append({
            "image": {
                "format": "jpeg",
                "source": {"bytes": base64.b64encode(retrieved_bytes).decode("utf-8")}
            }
        })

        content_blocks.append({
            "text": """
Analyze IMAGE A (Query) and IMAGE B (Retrieved) to verify visual relevance.

Objective: Determine if these two images are visually related or if this retrieval is a false positive.

Evaluate the connection:
- Direct match
- Strong relation
- Weak relation
- No relation

Output: 
Output a short analysis of each image.
Provide a one-sentence summary of the relationship.
"""
        })

        body = json.dumps({
            "inferenceConfig": {
                "max_new_tokens": 800,
                "temperature": 0.0
            },
            "messages": [
                {
                    "role": "user",
                    "content": content_blocks
                }
            ]
        })

        response = bedrock.invoke_model(
            modelId="amazon.nova-pro-v1:0",
            body=body
        )

        response_body = json.loads(response.get("body").read())
        return response_body["output"]["message"]["content"][0]["text"]

    except Exception as e:
        return f"Error comparing {query_filename} and {retrieved_filename}: {str(e)}"

IMAGE_KB_PROMPT = """ 
Retrieve the most relevant images related to the image using the image_retrieve tool.
Pass the image path (PNG, JPEG/JPG, GIF, or WebP formats) from the query into the image_path parameter.
For every file path or filename returned by 'image_retrieve', you MUST call 'get_cloudfront_url' to generate a valid access link.

Guidelines:
Make sure the full image path is passed, and not just the filename.
Return the full filepaths for the matching images if they are found.
If the top result scores end in a tie, return all of the results. 
If no image is found, or no image path is provided, return: IMAGE_NOT_AVAILABLE.
If retrieve returns no results or an error, return: INFO_NOT_AVAILABLE.
"""

IMAGE_READER_PROMPT = """ 
Analyze the query image and retrieved images using the get_image_comparison tool.
For each image analysis, pass the query image path (PNG, JPEG/JPG, GIF, or WebP formats) into the query_filename parameter and each image one at a time in the retrieved_filename parameter.

Guidelines: 
There must be at least two images analyzed: the query image and at least one retrieved image.
If the query image path is missing, or if the retrieval results contain no valid image paths, return: IMAGE_NOT_AVAILABLE.
If the images compared are completely unrelated, state this.
"""

SYNTHESIS_PROMPT_2 = """
Role:
Synthesize a final answer based on visual and knowledge base information.
If the results aren't conclusive, state this.

Guidelines:
Combine visual analysis with metadata for the final answer.
Report discrepancies between visual and metadata observations.
"""

@tool 
def get_image_input(query: str) -> str:
    """
    Process image inputs by retrieving archival matches and performing visual validation.
    """
    limit_hook = LimitToolCounts(max_tool_counts={"image_retrieve": 3})

    retrieval_agent = Agent(model=bedrock_model,
        system_prompt=IMAGE_KB_PROMPT, tools=[image_retrieve, get_cloudfront_url], hooks=[limit_hook])
    
    visual_agent = Agent(model=bedrock_model,
        system_prompt=IMAGE_READER_PROMPT, tools=[get_image_comparison])
    
    synthesis_agent = Agent(model=bedrock_model,
        system_prompt=SYNTHESIS_PROMPT_2)

    kb_results = retrieval_agent(f"From the image in the query, retrieve the best match image(s). Query: {query}.")
    
    if not str(kb_results).strip():
        return "The retrieval system failed to return a response. Please try again."
    if "image_not_available" in str(kb_results).lower():
        return f"No image path was detected in your request: '{query}'."
    if "info_not_available" in str(kb_results).lower():
        return f"I'm sorry, I couldn't find a specific image in our records for '{query}'."
    
    validation_results = visual_agent(
        f"Compare the user's image in the query with these archival images and URLs: {kb_results}. "
        f"Query: {query}"
    )

    if "image_not_available" in str(validation_results).lower():
        return "Visual validation failed because the input image could not be processed."

    response = synthesis_agent(f"Synthesize a final result for this query: {query}. "
                               f"Knowledge base metadata: {str(kb_results)}. "
                               f"Visual validation analysis: {str(validation_results)}.")
    return response