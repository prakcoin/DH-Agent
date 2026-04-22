"""
One-time script to populate an S3 vector bucket with image embeddings.

For each image in aw04-data/images/, calls Nova Multimodal Embeddings to
produce a 3072-dim image vector, then stores it in the target S3 vector bucket.

Usage:
    uv run python scripts/populate_image_vectors.py \
        --vector-bucket <bucket-name> \
        --index-name <index-name> \
        [--create]   # pass to create the bucket + index if they don't exist yet
"""

import argparse
import base64
import json
import os
import time
import boto3
from botocore.exceptions import ClientError

REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = "aw04-data"
IMAGE_PREFIX = "images/"
MODEL_ID = "amazon.nova-2-multimodal-embeddings-v1:0"
EMBEDDING_DIM = 3072
BATCH_SIZE = 10

s3 = boto3.client("s3", region_name=REGION)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
s3vectors = boto3.client("s3vectors", region_name=REGION)


def embed_image(image_bytes: bytes, image_format: str) -> list[float]:
    body = json.dumps({
        "schemaVersion": "nova-multimodal-embed-v1",
        "taskType": "SINGLE_EMBEDDING",
        "singleEmbeddingParams": {
            "embeddingPurpose": "IMAGE_RETRIEVAL",
            "embeddingDimension": EMBEDDING_DIM,
            "image": {
                "detailLevel": "STANDARD_IMAGE",
                "format": image_format,
                "source": {
                    "bytes": base64.b64encode(image_bytes).decode("utf-8")
                }
            }
        }
    })

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=body,
        accept="application/json",
        contentType="application/json"
    )

    result = json.loads(response["body"].read())
    return result["embeddings"][0]["embedding"]


def list_images() -> list[str]:
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=IMAGE_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith((".jpg", ".jpeg", ".png")):
                keys.append(key)
    return keys


def create_bucket_and_index(vector_bucket: str, index_name: str):
    try:
        s3vectors.create_vector_bucket(vectorBucketName=vector_bucket)
        print(f"Created vector bucket: {vector_bucket}")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("ConflictException", "BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
            print(f"Vector bucket already exists: {vector_bucket}")
        else:
            raise

    try:
        s3vectors.create_index(
            vectorBucketName=vector_bucket,
            indexName=index_name,
            dataType="float32",
            dimension=EMBEDDING_DIM,
            distanceMetric="cosine"
        )
        print(f"Created index: {index_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "IndexAlreadyExists":
            print(f"Index already exists: {index_name}")
        else:
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vector-bucket", required=True)
    parser.add_argument("--index-name", required=True)
    parser.add_argument("--create", action="store_true", help="Create bucket and index if they don't exist")
    args = parser.parse_args()

    if args.create:
        create_bucket_and_index(args.vector_bucket, args.index_name)

    image_keys = list_images()
    print(f"Found {len(image_keys)} images to index")

    batch = []
    for i, key in enumerate(image_keys):
        filename = key.split("/")[-1]
        fmt = filename.rsplit(".", 1)[-1].lower()
        if fmt == "jpg":
            fmt = "jpeg"

        try:
            image_bytes = s3.get_object(Bucket=S3_BUCKET, Key=key)["Body"].read()
            embedding = embed_image(image_bytes, fmt)

            batch.append({
                "key": filename,
                "data": {"float32": embedding},
                "metadata": {"filename": filename}
            })

            print(f"[{i+1}/{len(image_keys)}] Embedded {filename}")

        except Exception as e:
            print(f"[{i+1}/{len(image_keys)}] FAILED {filename}: {e}")
            continue

        if len(batch) >= BATCH_SIZE:
            s3vectors.put_vectors(
                vectorBucketName=args.vector_bucket,
                indexName=args.index_name,
                vectors=batch
            )
            print(f"  Stored batch of {len(batch)}")
            batch = []
            time.sleep(0.5)

    if batch:
        s3vectors.put_vectors(
            vectorBucketName=args.vector_bucket,
            indexName=args.index_name,
            vectors=batch
        )
        print(f"  Stored final batch of {len(batch)}")

    print("Done.")


if __name__ == "__main__":
    main()
