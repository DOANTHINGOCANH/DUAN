
from django.contrib.auth.models import User
from django.db import models

class Notification(models.Model): # thông báo về tin tức sự kiện
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    def __str__(self):
        return self.title

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Tên phòng ban
    created_at = models.DateTimeField(auto_now_add=True)  # Ngày tạo

    def __str__(self):
        return self.name

class EmployeeProfile(models.Model): # hồ sơ nhân viên
    employee_code = models.CharField(max_length=20, primary_key=True)  # Thay đổi max_length nếu cần
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    ethnicity = models.CharField(max_length=50)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    working_unit = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    def __str__(self):
        return self.employee_code

class Group(models.Model): #Nhóm nhắn tin
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')

    def __str__(self):
        return self.name

class GroupMember(models.Model): #Thành viên trong từng nhóm
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_members')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['group', 'user'], name='unique_group_member')
        ]
    def __str__(self):
        return f"{self.user.username} in {self.group.name}"

class Message(models.Model):
    TEXT = 'text'
    IMAGE = 'image'
    VIDEO = 'video'
    FILE = 'file'

    MESSAGE_TYPE_CHOICES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
        (FILE, 'File'),
    ]
    text = models.TextField(blank=True, null=True)  # Nội dung tin nhắn (nếu là văn bản)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')  # Người gửi
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE, related_name='messages')  # Nhóm gửi tin nhắn (nếu có)
    recipient = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='received_messages')  # Người nhận (nếu là tin nhắn cá nhân)
    created_at = models.DateTimeField(auto_now_add=True)  # Thời gian gửi tin nhắn
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default=TEXT)  # Loại tin nhắn
    def __str__(self):
        return f"Message from {self.sender.username} to {self.group.name if self.group else self.recipient.username}"

class Attachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')  # Tệp đính kèm
    file_type = models.CharField(max_length=50)  # Loại tệp (ví dụ: image/jpeg, application/pdf)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for Message {self.message.id}"



class Post(models.Model):
    content = models.TextField()
    image = models.ImageField(upload_to='images/', blank=True, null=True)  # Hình ảnh bài viết
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.content[:20]}..."

class Comment(models.Model):
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.content[:20]}..."

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    def __str__(self):
        return f"{self.user.username} liked {self.post.content[:20]}..."
