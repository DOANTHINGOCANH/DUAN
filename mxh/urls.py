from django.urls import path
from .views import *
from django.views.generic import TemplateView
urlpatterns = [
   path('login/', login_view, name='login'),
   path('logout/', logout_view, name='logout'),
   path('home/', home, name='home'),
   path('account_settings/',account_settings, name='account_settings' ),
   path('notifications/', notification_list, name='notification_list'),
   path('notifications/<int:pk>/', notification_detail, name='notification_detail'),
   path('notifications/create/', notification_create, name='notification_create'),
   path('notifications/update/<int:pk>/', notification_update, name='notification_update'),
   path('api/search_users/', search_users, name='search_users'),
   path('messages/group/<int:group_id>/', group_chat_view, name='group_chat'),
   path('messages/user/<int:user_id>/', user_chat_view, name='user_chat'),
   path('employee/<str:employee_code>/', employee_detail, name='employee_detail'),
   path('employees/', employee_list, name='employee_list'),
   path('employee/<str:employee_code>/update/', employee_update, name='employee_update'),
   path('messages/', message_list, name='message_list'),
   path('messages/create_group/', create_group, name='create_group'),
   path('messages/update_group/<int:group_id>/', create_group, name='update_group'),
   path('search_users_groups/', search_users_and_groups, name='search_users_groups'),
   path("", TemplateView.as_view(template_name="intro.html")),
   path('search/', search_view, name='search'),
   path('post/', post, name='post'),
   path('post/new/', post_create, name='post_create'),
   path('post/<int:pk>/delete/', post_delete, name='post_delete'),
   path('comment/<int:pk>/delete', comment_delete, name='comment_delete'),
   path('search/', search_posts, name='search_posts'),
   path('profile/<str:username>/', user_profile, name='user_profile'),
   path('post/<int:pk>/edit/', post_edit, name='post_edit'),
   path('post/<int:pk>/', post_detail, name='post_detail'),
   path('like/', like_post, name='like_post'),
]

