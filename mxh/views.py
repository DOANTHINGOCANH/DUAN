from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.contrib.messages import get_messages
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404,redirect
from .forms import *
from .models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.db.models import Q
from .models import Group, Message, User
from django.utils.timezone import now

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:

        form = CustomAuthenticationForm(initial={'username': '', 'password': ''})
    return render(request, 'login.html', {'form': form})

@never_cache
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login')

@never_cache
@login_required
def search_view(request):
    query = request.GET.get('q', '').strip()  # Lấy từ khóa tìm kiếm từ request
    results = {}

    if query:
        # Tìm kiếm thông báo
        notifications = Notification.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

        # Tìm kiếm nhân viên
        employees = EmployeeProfile.objects.filter(
            Q(employee_code__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(working_unit__icontains=query)
        )

        # Tìm kiếm bài viết
        posts = Post.objects.filter(
            Q(content__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

        # Kết quả tìm kiếm được nhóm lại
        results = {
            'notifications': notifications,
            'employees': employees,
            'posts': posts,
        }

    return render(request, 'search_results.html', {
        'query': query,
        'results': results,
    })

@never_cache
@login_required
def home(request):
    username = request.user.username if request.user.is_authenticated else None
    return render(request, 'home.html', {'username': username})

@never_cache
@login_required
def account_settings(request):
    user = request.user
    employee_profile, created = EmployeeProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')

            # Kiểm tra các trường không để trống
            if not first_name or not last_name or not email:
                messages.error(request, "Các trường không được để trống, yêu cầu nhập lại!")
                return render(request, 'account_settings.html', {
                    'user': user,
                    'employee_profile': employee_profile,
                })

            # Cập nhật các trường firstname, lastname và email
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            messages.success(request, "Cập nhật thông tin thành công!")
            return redirect('account_settings')

        elif 'update_password' in request.POST:
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not old_password or not new_password or not confirm_password:
                messages.error(request, "Các trường không được để trống, yêu cầu nhập lại!")
                return render(request, 'account_settings.html', {
                    'user': user,
                    'employee_profile': employee_profile,
                })

            if user.check_password(old_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, "Cập nhật mật khẩu thành công!")
                    return redirect('login')
                else:
                    messages.error(request, "Xác nhận mật khẩu không trùng khớp, yêu cầu nhập lại!")
            else:
                messages.error(request, "Mật khẩu cũ không chính xác!")

    # Đảm bảo luôn trả về phản hồi hợp lệ
    return render(request, 'account_settings.html', {
        'user': user,
        'employee_profile': employee_profile,
    })

@never_cache
@login_required
def notification_list(request):
    notifications = Notification.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        notifications = notifications.filter(title__icontains=search_query)
    if not notifications.exists():
        messages.info(request, 'Không tìm thấy thông báo nào phù hợp với tìm kiếm của bạn!')

    # Sắp xếp thông báo theo thời gian
    notifications = notifications.order_by('-created_at')

    # Tính thời gian hiển thị
    for notification in notifications:
        time_diff = now() - notification.created_at
        if time_diff.days >= 1:
            notification.time_display = f"{time_diff.days} ngày trước"
        elif time_diff.seconds >= 3600:
            notification.time_display = f"{time_diff.seconds // 3600} giờ trước"
        else:
            notification.time_display = f"{time_diff.seconds // 60} phút trước"

    return render(request, 'list.html', {'notifications': notifications})

@never_cache
@login_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    return render(request, 'detail.html', {'notification': notification})

@never_cache
@login_required
def notification_create(request):
    if request.user.is_staff:  # Kiểm tra xem người dùng có phải là manager không
        if request.method == 'POST':
            form = NotificationForm(request.POST)
            if form.is_valid():
                notification = form.save(commit=False)
                notification.user = request.user
                notification.save()
                messages.success(request, f'Đăng thông báo thành công!')
                return redirect('notification_list')
        else:
            form = NotificationForm()
        return render(request, 'create.html', {'form': form})
    else:
        return redirect('notification_list')

@never_cache
@login_required
def notification_update(request, pk):
    # Lấy thông báo dựa trên primary key
    notification = get_object_or_404(Notification, pk=pk)

    # Kiểm tra quyền chỉnh sửa
    if request.user == notification.user or request.user.is_staff:
        if request.method == 'POST':
            form = NotificationForm(request.POST, instance=notification)
            if form.is_valid():
                # Cập nhật thời gian `created_at` khi lưu
                notification = form.save(commit=False)
                notification.created_at = now()  # Gán thời gian hiện tại
                notification.save()
                messages.success(request, 'Cập nhật thông báo thành công!')
                return redirect('notification_list')
        else:
            form = NotificationForm(instance=notification)
        return render(request, 'update.html', {'form': form, 'notification': notification})
    else:
        messages.error(request, 'Bạn không có quyền sửa thông báo này!')
        return redirect('notification_list')

@never_cache
@login_required
def group_chat_view(request, group_id):
    group = Group.objects.get(id=group_id)

    if not GroupMember.objects.filter(group=group, user=request.user).exists():
        return HttpResponseForbidden("Bạn không phải là thành viên của nhóm này.")

    if request.method == 'POST':
        text = request.POST.get('text')
        message = Message.objects.create(
            text=text,
            sender=request.user,
            group=group,
            message_type=Message.TEXT
        )

        if request.FILES.getlist('attachments'):
            for file in request.FILES.getlist('attachments'):
                file_type = 'image' if file.content_type.startswith('image/') else 'file'
                Attachment.objects.create(
                    message=message,
                    file=file,
                    file_type=file_type
                )

        return redirect('group_chat', group_id=group.id)  # Redirect đến trang nhóm chat
    messages = Message.objects.filter(group=group).select_related('sender').prefetch_related('attachments')
    return render(request, 'group_chat.html', {'group': group, 'messages': messages})

@never_cache
@login_required
def user_chat_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return HttpResponseForbidden("Bạn không thể chat với chính mình.")
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text or request.FILES.getlist('attachments'):
            message = Message.objects.create(
                text=text,
                sender=request.user,
                recipient=target_user,
                message_type=Message.TEXT
            )
            for file in request.FILES.getlist('attachments'):
                file_type = 'image' if file.content_type.startswith('image/') else 'file'
                Attachment.objects.create(
                    message=message,
                    file=file,
                    file_type=file_type
                )
        return redirect('user_chat', user_id=target_user.id)
    messages = Message.objects.filter((Q(sender=request.user, recipient=target_user) | Q(sender=target_user, recipient=request.user))).select_related('sender', 'recipient').prefetch_related('attachments').order_by('created_at')

    return render(request, 'user_chat.html', {'user': target_user, 'messages': messages})

@never_cache
@login_required
def create_group(request, group_id=None):
    users = User.objects.exclude(id=request.user.id)
    group = None
    is_edit = False
    selected_users = []
    if group_id:
        group = get_object_or_404(Group, id=group_id)
        is_edit = True
        selected_users = group.members.values_list('user', flat=True)
    if request.method == 'POST':
        if group:
            form = GroupForm(request.POST, instance=group)
        else:
            form = GroupForm(request.POST)

        if form.is_valid():
            group = form.save(commit=False)
            if not group.id:
                group.created_by = request.user
            group.save()
            GroupMember.objects.filter(group=group).delete()  # Xóa thành viên cũ nếu có
            GroupMember.objects.create(group=group, user=request.user)  # Người tạo nhóm
            members = form.cleaned_data['members']
            for user in members:
                GroupMember.objects.create(group=group, user=user)
            if group_id:
                messages.success(request, "Sửa nhóm thành công!")
            else:
                messages.success(request, "Tạo nhóm thành công!")
            return redirect('group_chat', group_id=group.id)
    else:
        if group:
            form = GroupForm(instance=group)
        else:
            form = GroupForm()
    storage = get_messages(request)
    return render(
        request,
        'create_group.html',
        {
            'form': form,
            'users': users,
            'selected_users': selected_users,
            'is_edit': is_edit,
            'flash_messages': storage,
        }
    )


@never_cache
@login_required
def search_users(request):
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        if query:
            users = User.objects.filter(username__icontains=query).values('id', 'username')[:10]
            return JsonResponse({'users': list(users)}, safe=False)
        return JsonResponse({'users': []}, safe=False)
def employee_detail(request, employee_code):
    employee = EmployeeProfile.objects.get(employee_code=employee_code)
    context = {
        'employee': employee
    }
    return render(request, 'hoso_detail.html', context)

@never_cache
@login_required
def employee_list(request):
    departments = Department.objects.all()
    selected_department = request.GET.get('department', None)

    if selected_department:
        employees = EmployeeProfile.objects.filter(department=selected_department)
    else:
        employees = EmployeeProfile.objects.all()

    context = {
        'employees': employees,
        'departments': departments,
        'selected_department': selected_department
    }
    return render(request, 'employee_list.html', context)

@never_cache
@login_required
@user_passes_test(lambda u: u.is_superuser or u == EmployeeProfile.objects.get(user=u).user)
def employee_update(request, employee_code):
    employee = get_object_or_404(EmployeeProfile, employee_code=employee_code)

    if request.user != employee.user and not request.user.is_staff:
        messages.error(request, "Bạn không được phép chỉnh sửa thông tin của nhân viên này.")
        return redirect('employee_detail', employee_code=employee_code)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thông tin nhân viên được cập nhật thành công!')
            return redirect('employee_detail', employee_code=employee_code)
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'employee_update.html', {'form': form})

@never_cache
@login_required
def message_list(request):
    recent_messages = Message.objects.all().order_by('-created_at')
    conversations = {}

    personal_messages = Message.objects.filter(
        (Q(sender=request.user) | Q(recipient=request.user))

    ).order_by('-created_at')

    for msg in personal_messages:
        user_key = msg.sender if msg.sender != request.user else msg.recipient
        if user_key not in conversations:
            conversations[user_key] = {
                'type': 'personal',
                'user': user_key,
                'last_message': msg.text,
                'time': msg.created_at,
                'sender': msg.sender,
            }
        elif msg.created_at > conversations[user_key]['time']:
            conversations[user_key]['last_message'] = msg.text
            conversations[user_key]['time'] = msg.created_at
            conversations[user_key]['sender'] = msg.sender
    group_messages = Message.objects.filter(group__members__user=request.user).order_by('-created_at')
    for msg in group_messages:
        group_key = msg.group
        if group_key not in conversations:
            conversations[group_key] = {
                'type': 'group',
                'group': group_key,
                'last_message': msg.text,
                'time': msg.created_at,
                'sender': msg.sender,
            }
        elif msg.created_at > conversations[group_key]['time']:
            conversations[group_key]['last_message'] = msg.text
            conversations[group_key]['time'] = msg.created_at
            conversations[group_key]['sender'] = msg.sender

    sorted_conversations = sorted(conversations.values(), key=lambda x: x['time'], reverse=True)

    context = {
        'conversations': sorted_conversations,
    }

    return render(request, 'message_list.html', context)


def search_users_and_groups(request):
    query = request.GET.get('query', '').strip()
    current_user = request.user

    # Tìm kiếm người dùng theo username, first_name và last_name
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).exclude(id=current_user.id).values('id', 'username', 'first_name', 'last_name')

    # Tìm kiếm nhóm theo tên và kiểm tra các thành viên
    groups = Group.objects.filter(
        Q(name__icontains=query),
        members__user=current_user
    ).values('id', 'name')

    return JsonResponse({
        'users': list(users),
        'groups': list(groups),
    })

#view danh sách bài viết:
@login_required
def post(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'post.html', {'posts': posts})

#view danh sách bài viết:
@login_required
def post(request):
    posts = Post.objects.all().order_by('-created_at')
    for post in posts:
        post.time_display = (
            f"{(now() - post.created_at).days} ngày trước"
            if (now() - post.created_at).days >= 1
            else f"{(now() - post.created_at).seconds // 3600} giờ trước"
            if (now() - post.created_at).seconds >= 3600
            else f"{(now() - post.created_at).seconds // 60} phút trước"
        )
    return render(request, 'post.html', {'posts': posts})

# View tạo bài viết mới:
@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('post')
    else:
        form = PostForm()
    return render(request, 'post_create.html', {'form': form})

#Xóa bài viết:
@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, user=request.user)
    post.delete()
    return redirect('post')

#Tạo bình luận:
@login_required
def comment_create(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            return redirect('post')
    else:
        form = CommentForm()
    return render(request, 'comment_create.html', {'form': form, 'post': post})

#Xóa bình luận:
@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk, user=request.user)
    comment.delete()
    return redirect('post')

#like bài viết:
@login_required
def like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like_obj, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like_obj.delete()
        like_count = Like.objects.filter(post=post).count()
    return redirect('post')

#Tìm kiếm bài viết:
@login_required
def search_posts(request):
    form = PostSearchForm(request.GET)  # Nhận từ khóa từ phương thức GET
    posts = Post.objects.all()  # Lấy toàn bộ bài viết mặc định
    query = ""
    if form.is_valid():
        query = form.cleaned_data.get('query')  # Lấy từ khóa từ form
        if query:
            posts = posts.filter(content__icontains=query).order_by('-created_at')  # Lọc theo tiêu đề bài viết

    return render(request, 'search_posts.html', {'form': form, 'posts': posts, 'query': query})

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(user=user)

    context = {
        'profile_user': user,
        'user_posts': user_posts,
    }
    return render(request, 'user_profile.html', context)

@login_required
def post_edit (request, pk):
    post = get_object_or_404(Post, pk=pk, user=request.user)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post')  # Redirect về trang chủ hoặc nơi khác
    else:
        form = PostForm(instance=post)
    return render(request, 'post_edit.html', {'form': form})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()

    # Nếu là yêu cầu AJAX
    if request.is_ajax():
        return JsonResponse({
            'post_content': post.content,
            'comments': [{'author': comment.author.username, 'text': comment.text} for comment in comments],
            'comment_count': comments.count(),
        })

    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
    })