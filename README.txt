- Vô folder tracker chạy python server.py
- Vô folder seeder
  + bỏ các file muốn chuyển vô thư mục store
  + chạy seeder 1 lần duy nhất
  + copy torrent_file.torrent ở thư mục seeder qua thư mục leecher
  + nếu chạy lỗi muốn chạy lại seeder thì xóa các tệp rác trong thư mục store đi
- Vô folder leecher 
  + copy cả folder ra thành nhiều bản trước khi chạy nếu muốn chạy nhiều leecher
  + chạy lệnh python leecher.py
  + với mỗi folder leecher copy ra thì thay auth token ở dòng 11 trong file leecher.py bằng auth token mới
  + chạy bao nhiêu leecher cũng dc
  + giờ leecher đã có thể nhận file và gửi lại file đã nhận

