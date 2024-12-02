from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import *

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Tên người dùng')
    password = forms.CharField(label='Mật khẩu', widget=forms.PasswordInput)

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'content']


class GroupForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Thành viên"
    )

    class Meta:
        model = Group
        fields = ['name', 'members']
        labels = {
            'name': 'Tên nhóm',
        }
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text', 'recipient', 'group']

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = '__all__'
        widgets = {
            'employee_code': forms.TextInput(attrs={'readonly': True}),

        }
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

class PostSearchForm(forms.Form):
    query = forms.CharField(label='Tìm kiếm', max_length=100, required=False)

