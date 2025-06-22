import boto3
import os
from PIL import Image
import mimetypes
from io import BytesIO
import sys
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
s3 = boto3.client('s3')
 
def lambda_handler(event, context):
    for record in event['Records']:
        # Get bucket and bucket arn
        bucket = record['s3']['bucket']['name']
        # File uploaded 
        key = record['s3']['object']['key']
        filename = os.path.basename(key)
        name, ext = os.path.splitext(filename)

        # Skip all files having pattern: image-100x100.jpg to prevent looping
        pattern = re.compile(r".*-\d+x\d+")
        if pattern.match(name):
            continue

        # Only process images
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            continue

        if name.lower().endswith(('-100x100', '-150x150')):
            continue
        
        # Lấy MIME type theo đuôi của key (file name)
        content_type, _ = mimetypes.guess_type(key)
        if content_type is None:
            content_type = 'application/octet-stream'

        try:
            # Lấy file từ S3
            response = s3.get_object(Bucket=bucket, Key=key)
            image_content = response['Body'].read()
            
            # Resize ảnh
            resized_images = resize_image(image_content)
            
            # Lưu ảnh đã resize lại S3
            for size, img_data in resized_images.items():
                new_name, _ = os.path.splitext(key)
                new_key = f"{new_name}-{size}{ext}"
                s3.put_object(
                    Bucket=bucket,
                    Key=new_key,
                    Body=img_data,
                    ContentType=content_type
                )
                print(f"Resized image saved: s3://{bucket}/{new_key}")
                
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            raise e

    return {
        'statusCode': 200,
        'body': f"Processed {len(event['Records'])} images."
    }

def resize_image(image_content, sizes=[(100, 100), (150, 150)]):
    """Resize ảnh theo các kích thước chỉ định"""
    results = {}
    
    # Mở ảnh từ dữ liệu nhị phân
    with Image.open(BytesIO(image_content)) as img:
        # Chuyển đổi sang RGB nếu cần
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGBA')
        
        fmt = img.format or 'JPEG'
        
        original_size = img.size
        # Tạo ảnh resize cho từng kích thước
        for target_size in sizes:
            # Tính tỷ lệ crop
            target_width, target_height = target_size
            ratio = max(
                target_width / original_size[0],
                target_height / original_size[1]
            )
            new_size = (
                int(original_size[0] * ratio),
                int(original_size[1] * ratio)
            )

            # Resize ảnh
            resized = img.resize(new_size, Image.LANCZOS)
            
            # Cắt phần thừa ở giữa
            left = (new_size[0] - target_width) / 2
            top = (new_size[1] - target_height) / 2
            right = (new_size[0] + target_width) / 2
            bottom = (new_size[1] + target_height) / 2
            resized = resized.crop((left, top, right, bottom))

            # Lưu ảnh vào buffer
            buffer = BytesIO()
            resized.save(buffer, fmt, quality=95)
            buffer.seek(0)
            
            # Lưu kết quả với key là kích thước
            results[f"{target_width}x{target_height}"] = buffer.getvalue()
    
    return results