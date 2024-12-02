from django.contrib import admin
from .models import Notification, EmployeeProfile, Group, GroupMember, Message, Attachment, Post, Like, Comment, Department

# Đăng ký các model với Django Admin

# Đăng ký model Notification
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')  # Hiển thị tên, người dùng và thời gian tạo
    search_fields = ('title', 'content')  # Tìm kiếm thông báo

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')  # Hiển thị tên phòng ban và ngày tạo
    search_fields = ('name',)  # Tìm kiếm theo tên phòng ban

# Đăng ký model EmployeeProfile
@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_code', 'user', 'position', 'department', 'phone_number')  # Các thông tin cơ bản
    search_fields = ('employee_code', 'user__username', 'phone_number')  # Tìm kiếm theo mã nhân viên và tên người dùng

# Đăng ký model Group
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')  # Hiển thị tên nhóm, người tạo và thời gian tạo
    search_fields = ('name', 'created_by__username')  # Tìm kiếm theo tên nhóm và người tạo

# Đăng ký model GroupMember
@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'joined_at')  # Hiển thị nhóm, người dùng và thời gian tham gia
    search_fields = ('group__name', 'user__username')  # Tìm kiếm theo tên nhóm và tên người dùng

# Đăng ký model Message
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'group', 'created_at', 'message_type','text')  # Hiển thị thông tin tin nhắn
    search_fields = ('sender__username', 'recipient__username', 'group__name','text')  # Tìm kiếm theo người gửi, người nhận và nhóm

# Đăng ký model Attachment
@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('message', 'file', 'file_type', 'uploaded_at')  # Hiển thị thông tin tệp đính kèm
    search_fields = ('message__id', 'file_type')  # Tìm kiếm theo ID tin nhắn và loại tệp

# Đăng ký model Post
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'likes_number', 'comments_number')  # Hiển thị bài viết và số lượt thích, bình luận
    search_fields = ('user__username', 'content')  # Tìm kiếm theo người tạo và nội dung

    def likes_number(self, obj):
        return obj.likes.count()  # Số lượt thích

    likes_number.short_description = 'Likes'

    def comments_number(self, obj):
        return obj.comments.count()  # Số bình luận

    comments_number.short_description = 'Comments'
# Đăng ký model LikePost
@admin.register(Like)
class LikePostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post')  # Hiển thị người thích và bài viết
    search_fields = ('user__username', 'post__id')  # Tìm kiếm theo người dùng và bài viết


# Đăng ký model CommentPost
@admin.register(Comment)
class CommentPostAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'content', 'created_at')  # Hiển thị bài viết, người bình luận và nội dung
    search_fields = ('post__id', 'user__username', 'content')  # Tìm kiếm theo bài viết, người dùng và nội dung