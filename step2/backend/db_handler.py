import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# --- Cấu hình kết nối ---
# Lấy thông tin từ lệnh của bạn
db_config = {
    'host': os.getenv("DB_HOST"),
    'port': int(os.getenv("DB_PORT")),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWD"), 
    'database': os.getenv("DB_DATABASE"), # Thay bằng tên CSDL bạn muốn kết nối
    
    # --- Cấu hình SSL quan trọng ---
    # Ánh xạ từ --ssl và --ssl-ca
    'ssl': {
        'ca': os.getenv("DB_SSL_CA_PATH")
    },
    
    # Tùy chọn: Trả về kết quả dưới dạng dictionary để dễ dàng chuyển sang JSON
    'cursorclass': pymysql.cursors.DictCursor
}

PRODUCT_GETTER_QUERY = '''
SELECT
    p.id as id,
    p.post_title as name,
    MAX(CASE WHEN pm.meta_key = '_stock' THEN pm.meta_value END) AS quantity,
    MAX(CASE WHEN pm.meta_key = '_stock_status' THEN pm.meta_value END) AS stockStatus,
    MAX(CASE WHEN pm.meta_key = '_regular_price' THEN pm.meta_value END) AS regularPrice,
    MAX(CASE WHEN pm.meta_key = '_sale_price' THEN pm.meta_value END) AS salePrice,
    MAX(CASE WHEN pm.meta_key = '_low_stock_amount' THEN pm.meta_value END) AS lowStockAmount
FROM
    (SELECT id, post_title FROM wp_posts WHERE post_type = 'product' AND post_status = 'publish') AS p
JOIN
    wp_postmeta AS pm ON p.id = pm.post_id
WHERE
    pm.meta_key IN (
        '_stock', '_stock_status', '_regular_price',
        '_sale_price', '_low_stock_amount'
    )
GROUP BY
    p.id, p.post_title
ORDER BY
    p.id DESC
'''

ORDER_GETTER_QUERY = '''
SELECT
    orders.id AS id,
    orders.customer_id as customer_id,
    orders.status AS status,
    orders.total_amount AS totalCost,
    customer.username AS customer,
    orders.date_created_gmt AS date,
    JSON_ARRAYAGG(
        IF(items.product_id IS NOT NULL,
            JSON_OBJECT(
                'product_id', items.product_id,
                'post_title', item_posts.post_title,
                'quantity', items.product_qty
            ),
            NULL
        )
    ) AS items
FROM
    wp_wc_orders AS orders
LEFT JOIN
    wp_wc_customer_lookup AS customer ON orders.customer_id = customer.user_id
LEFT JOIN
    wp_wc_order_product_lookup AS items ON orders.id = items.order_id
LEFT JOIN
    wp_posts AS item_posts ON items.product_id = item_posts.id
WHERE
    orders.status IN ('wc-processing', 'wc-completed', 'wc-cancelled')
    AND (item_posts.post_type = 'product' OR item_posts.id IS NULL)
GROUP BY
    orders.id,
    orders.status,
    orders.total_amount,
    customer.username,
    orders.date_created_gmt
ORDER BY
    orders.date_created_gmt DESC;
'''

def database_provider(query_message):
    # --- Kiểm tra kết nối ---
    connection = None
    results = []
    status = 404
    try:
        # Sử dụng **db_config để truyền tất cả các tham số vào hàm connect
        connection = pymysql.connect(**db_config)
        
        print("Kết nối đến AWS RDS MariaDB thành công!")
        
        with connection.cursor() as cursor:
            cursor.execute(query_message)
            results = cursor.fetchall()
            status = 200

    except pymysql.MySQLError as e:
        print(f"Lỗi kết nối đến MariaDB: {e}")

    finally:
        # Đảm bảo kết nối luôn được đóng
        if connection:
            connection.close()
            print("Đã đóng kết nối.")
    
    return results, status