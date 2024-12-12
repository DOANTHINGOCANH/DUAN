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
from .models import Group, Message, User
from django.utils.timezone import now
from unidecode import unidecode
from django.db.models import F, Q, Value, CharField
from django.db.models.functions import Concat
import re

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
   query = request.GET.get('q', '').strip()
   results = {}
   if query:
       normalized_query = unidecode(query).lower()
       notifications = Notification.objects.filter(
           Q(title__icontains=query) |
           Q(content__icontains=query)
       )
       employees = EmployeeProfile.objects.annotate(
           full_name=Concat(
               F('user__first_name'),
               Value(' '),
               F('user__last_name'),
               output_field=CharField()
           )
       ).filter(
           Q(employee_code__icontains=query) |
           Q(full_name__icontains=query) |
           Q(user__username__icontains=query) |
           Q(working_unit__icontains=query) |
           Q(department__name__icontains=query)
       )
       posts = Post.objects.annotate(
           author_name=Concat(
               F('user__first_name'),
               Value(' '),
               F('user__last_name'),
               output_field=CharField()
           )
       ).filter(
           Q(content__icontains=query) |
           Q(author_name__icontains=query)
       )
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

            if not first_name or not last_name or not email:
                messages.error(request, "Các trường không được để trống, yêu cầu nhập lại!")
                return render(request, 'account_settings.html', {
                    'user': user,
                    'employee_profile': employee_profile,
                })

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

            # Kiểm tra các trường mật khẩu không để trống
            if not old_password or not new_password or not confirm_password:
                messages.error(request, "Các trường không được để trống, yêu cầu nhập lại!")
                return render(request, 'account_settings.html', {
                    'user': user,
                    'employee_profile': employee_profile,
                })

            # Kiểm tra mật khẩu cũ
            if user.check_password(old_password):
                # Kiểm tra điều kiện mật khẩu mới
                password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+={}\[\]:;"\'<>,.?/\\|`~]).{8,}$'
                if not re.match(password_regex, new_password):
                    messages.error(request,
                                   "Mật khẩu phải đạt độ dài tối thiểu 8 ký tự, có ít nhất 1 chữ cái viết hoa, 1 chữ số, 1 kí tự đặc biệt và 1 chữ cái thường!")
                    return render(request, 'account_settings.html', {
                        'user': user,
                        'employee_profile': employee_profile,
                    })

                # Kiểm tra mật khẩu xác nhận
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, "Cập nhật mật khẩu thành công!")
                    return redirect('login')
                else:
                    messages.error(request, "Xác nhận mật khẩu không trùng khớp, yêu cầu nhập lại!")
            else:
                messages.error(request, "Mật khẩu cũ không chính xác!")

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
   notifications = notifications.order_by('-created_at')
   for notification in notifications:
       time_diff = now() - notification.created_at
       if time_diff.days > 2:
           notification.time_display = notification.created_at.strftime("%d/%m/%Y")
       elif time_diff.days >= 1:
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
   time_diff = now() - notification.created_at
   if time_diff.days > 2:
       notification.time_display = notification.created_at.strftime("%d/%m/%Y")
   elif time_diff.days >= 1:
       notification.time_display = f"{time_diff.days} ngày trước"
   elif time_diff.seconds >= 3600:
       notification.time_display = f"{time_diff.seconds // 3600} giờ trước"
   else:
       notification.time_display = f"{time_diff.seconds // 60} phút trước"
   return render(request, 'detail.html', {'notification': notification})


@never_cache
@login_required
def notification_create(request):
   if request.user.is_staff:
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
   notification = get_object_or_404(Notification, pk=pk)
   if request.user == notification.user or request.user.is_staff:
       if request.method == 'POST':
           form = NotificationForm(request.POST, instance=notification)
           if form.is_valid():
               notification = form.save(commit=False)
               notification.created_at = now()
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
       return redirect('group_chat', group_id=group.id)
   messages = Message.objects.filter(group=group).select_related('sender').prefetch_related('attachments')
   for message in messages:
       message.time_display = (
           message.created_at.strftime("%d/%m/%Y")
           if (now() - message.created_at).days > 2
           else f"{(now() - message.created_at).days} ngày trước"
           if (now() - message.created_at).days >= 1
           else f"{(now() - message.created_at).seconds // 3600} giờ trước"
           if (now() - message.created_at).seconds >= 3600
           else f"{(now() - message.created_at).seconds // 60} phút trước"
           if (now() - message.created_at).seconds >= 60
           else "Vừa xong"
       )
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
   for message in messages:
       message.time_display = (
           message.created_at.strftime("%d/%m/%Y")
           if (now() - message.created_at).days > 2
           else f"{(now() - message.created_at).days} ngày trước"
           if (now() - message.created_at).days >= 1
           else f"{(now() - message.created_at).seconds // 3600} giờ trước"
           if (now() - message.created_at).seconds >= 3600
           else f"{(now() - message.created_at).seconds // 60} phút trước"
           if (now() - message.created_at).seconds >= 60
           else "Vừa xong"
       )
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
           GroupMember.objects.filter(group=group).delete()
           GroupMember.objects.create(group=group, user=request.user)
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
       (Q(sender=request.user) | Q(recipient=request.user))).order_by('-created_at')
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

   for conversation in sorted_conversations:
       conversation['time_display'] = (
           conversation['time'].strftime("%d/%m/%Y")
           if (now() - conversation['time']).days > 2
           else f"{(now() - conversation['time']).days} ngày trước"
           if (now() - conversation['time']).days >= 1
           else f"{(now() - conversation['time']).seconds // 3600} giờ trước"
           if (now() - conversation['time']).seconds >= 3600
           else f"{(now() - conversation['time']).seconds // 60} phút trước"
           if (now() - conversation['time']).seconds >= 60
           else "Vừa xong"
       )

   context = {
       'conversations': sorted_conversations,
   }


   return render(request, 'message_list.html', context)


@never_cache
@login_required
def search_users_and_groups(request):
   query = request.GET.get('query', '').strip()
   current_user = request.user

   users = User.objects.filter(
       Q(username__icontains=query) |
       Q(first_name__icontains=query) |
       Q(last_name__icontains=query)
   ).exclude(id=current_user.id).values('id', 'username', 'first_name', 'last_name')

   groups = Group.objects.filter(
       Q(name__icontains=query),
       members__user=current_user
   ).values('id', 'name')


   return JsonResponse({
       'users': list(users),
       'groups': list(groups),
   })


@never_cache
@login_required
def post(request):
   posts = Post.objects.all().order_by('-created_at')
   for post in posts:
       post.time_display = (
           post.created_at.strftime("%d/%m/%Y")
           if (now() - post.created_at).days > 2
           else f"{(now() - post.created_at).days} ngày trước"
           if (now() - post.created_at).days >= 1
           else f"{(now() - post.created_at).seconds // 3600} giờ trước"
           if (now() - post.created_at).seconds >= 3600
           else f"{(now() - post.created_at).seconds // 60} phút trước"
           if (now() - post.created_at).seconds >= 60
           else "Vừa xong"
       )
   return render(request, 'post.html', {'posts': posts})



@never_cache
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


@never_cache
@login_required
def post_delete(request, pk):
   post = get_object_or_404(Post, pk=pk, user=request.user)
   post.delete()
   return redirect('post')





@never_cache
@login_required
def like_post(request):
   post_id = request.POST.get('post_id')
   post = Post.objects.get(id=post_id)
   like, created = Like.objects.get_or_create(user=request.user, post=post)


   if not created:
       like.delete()
       liked = False
   else:
       liked = True


   like_count = Like.objects.filter(post=post).count()
   return JsonResponse({'liked': liked, 'like_count': like_count})


@never_cache
@login_required
def comment_delete(request, pk):
   comment = get_object_or_404(Comment, pk=pk, user=request.user)
   post_pk = comment.post.pk
   comment.delete()
   return redirect('post_detail', pk=post_pk)


@never_cache
@login_required
def search_posts(request):
   form = PostSearchForm(request.GET)
   posts = Post.objects.all()
   query = ""
   if form.is_valid():
       query = form.cleaned_data.get('query')
       if query:
           posts = posts.filter(content__icontains=query).order_by('-created_at')

   return render(request, 'search_posts.html', {'form': form, 'posts': posts, 'query': query})


@never_cache
@login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(user=user).order_by('-created_at')

    for post in user_posts:
        post.time_display = (
            post.created_at.strftime("%d/%m/%Y")
            if (now() - post.created_at).days > 2
            else f"{(now() - post.created_at).days} ngày trước"
            if (now() - post.created_at).days >= 1
            else f"{(now() - post.created_at).seconds // 3600} giờ trước"
            if (now() - post.created_at).seconds >= 3600
            else f"{(now() - post.created_at).seconds // 60} phút trước"
            if (now() - post.created_at).seconds >= 60
            else "Vừa xong"
        )

    context = {
        'profile_user': user,
        'user_posts': user_posts,
    }
    return render(request, 'user_profile.html', context)

@never_cache
@login_required
def post_edit (request, pk):
   post = get_object_or_404(Post, pk=pk, user=request.user)
   if request.method == "POST":
       form = PostForm(request.POST, request.FILES, instance=post)
       if form.is_valid():
           form.save()
           return redirect('post_detail',pk=post.pk)
   else:
       form = PostForm(instance=post)
   return render(request, 'post_edit.html', {'form': form})


@never_cache
@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all().order_by('-created_at')
    post.time_display = (
        post.created_at.strftime("%d/%m/%Y")
        if (now() - post.created_at).days > 2
        else f"{(now() - post.created_at).days} ngày trước"
        if (now() - post.created_at).days >= 1
        else f"{(now() - post.created_at).seconds // 3600} giờ trước"
        if (now() - post.created_at).seconds >= 3600
        else f"{(now() - post.created_at).seconds // 60} phút trước"
        if (now() - post.created_at).seconds >= 60
        else "Vừa xong"
    )

    for comment in comments:
        comment.time_display = (
            comment.created_at.strftime("%d/%m/%Y")
            if (now() - comment.created_at).days > 2
            else f"{(now() - comment.created_at).days} ngày trước"
            if (now() - comment.created_at).days >= 1
            else f"{(now() - comment.created_at).seconds // 3600} giờ trước"
            if (now() - comment.created_at).seconds >= 3600
            else f"{(now() - comment.created_at).seconds // 60} phút trước"
            if (now() - comment.created_at).seconds >= 60
            else "Vừa xong"
        )
    if request.method == "POST" and 'like' in request.POST:
        if request.user.is_authenticated:
            like_instance = Like.objects.filter(user=request.user, post=post).first()
            if like_instance:
                like_instance.delete()
            else:
                Like.objects.create(user=request.user, post=post)

            is_liked = Like.objects.filter(user=request.user, post=post).exists()
            like_count = post.likes.count()

            return JsonResponse({
                'like_count': like_count,
                'is_liked': is_liked
            })


    if request.method == "POST" and 'comment' in request.POST:
        if request.user.is_authenticated:
            content = request.POST.get('content')
            if content:
                comment = Comment.objects.create(user=request.user, post=post, content=content)

                return JsonResponse({
                    'author': comment.user.first_name+" "+comment.user.last_name,
                    'content': comment.content,
                    'created_at': comment.created_at,
                    'comment_count': post.comments.count(),
                    'success': True
                })
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập để bình luận'})
    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
    })

