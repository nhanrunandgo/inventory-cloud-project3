**Lấy chứng chỉ Let's encrypt cho 1 domain bất kỳ**
cd step1
Chỉnh sửa trong .env
docker compose up -d nginx-cert
docker compose run --rm certbot
docker compose down

# Khi đó ctrinh sẽ tự động thêm chứng chỉ vào step2/certbot/ dùng cho step 2
**Vào step 2**
Chỉnh sửa file .env là domain đã đăng ký

**Frontend**
Chỉnh sửa link có trong index.html (ctrl+F và tìm html) thành địa chỉ domain đã đăng ký

**Backend**
Chỉnh sửa file .env
# Note: Có thể phải đổi quyền của /backend/ssh_key/rds-ca.pem bằng lệnh chmod 400 /backend/ssh_key/rds-ca.pem

**Khởi chạy**
docker compose up -d

**Dừng các service**
docker compose down