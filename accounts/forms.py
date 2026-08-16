from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.text import slugify

from .models import User, Student, ClassRoom


class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Class Six'})
        }


def _generate_username(full_name, guardian_phone):
    """full_name + phone থেকে একটা unique username বানায়।"""
    base = slugify(full_name) or 'student'
    suffix = ''.join(ch for ch in guardian_phone if ch.isdigit())[-4:]
    username = f"{base}-{suffix}" if suffix else base

    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}-{suffix}-{counter}" if suffix else f"{base}-{counter}"
        counter += 1

    return username


class StudentAddForm(forms.Form):
    """Teacher কোনো student-এর account বানাবে (public register নেই)।
    Password/email লাগবে না — student log in করতে পারবে না।"""

    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Mohammad Rahman'})
    )

    school_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Dhaka Government High School'})
    )

    classroom = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all()
    )

    guardian_phone_1 = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '01XXXXXXXXX'})
    )

    guardian_phone_2 = forms.CharField(
        max_length=20,
        required=False,          # ← False করা ভালো, model এও blank=True আছে
        widget=forms.TextInput(attrs={'placeholder': '01XXXXXXXXX (optional)'})
    )

    def save(self, commit=True):
        user = User(
            username=_generate_username(
                self.cleaned_data['full_name'],
                self.cleaned_data['guardian_phone_1'],
            ),
            role='student',
        )
        user.set_unusable_password()   # student login বন্ধ, তাই password লাগবে না

        if commit:
            user.save()
            Student.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                school_name=self.cleaned_data['school_name'],
                classroom=self.cleaned_data['classroom'],
                guardian_phone_1=self.cleaned_data['guardian_phone_1'],
                guardian_phone_2=self.cleaned_data['guardian_phone_2'],
                is_approved=True,   # ← teacher নিজেই add করছে, তাই সরাসরি approved
            )

        return user


class UserLoginForm(AuthenticationForm):

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'your_username'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )