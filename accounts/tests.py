from django.test import TestCase
from django.urls import reverse

from .models import User, ClassRoom, Student


class RegistrationEndpointTests(TestCase):
    def test_teacher_registration_endpoint_removed(self):
        response = self.client.get('/accounts/teacher/register/')
        self.assertEqual(response.status_code, 404)

    def test_student_registration_endpoint_removed(self):
        response = self.client.get('/accounts/student/register/')
        self.assertEqual(response.status_code, 404)

    def test_student_dashboard_endpoint_removed(self):
        response = self.client.get('/reports/dashboard/')
        self.assertEqual(response.status_code, 404)


class AuthorizationTests(TestCase):
    def setUp(self):
        self.room = ClassRoom.objects.create(name='Test Room')
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='pass12345',
            role='teacher',
        )

    def test_class_list_requires_login(self):
        response = self.client.get(reverse('class_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_add_student_requires_login(self):
        response = self.client.get(reverse('add_student'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_add_student_requires_teacher(self):
        self.client.login(username='teacher1', password='pass12345')
        response = self.client.get(reverse('add_student'))
        self.assertEqual(response.status_code, 200)


class AddClassTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher_add_class',
            password='pass12345',
            role='teacher',
        )

    def test_add_class_requires_login(self):
        response = self.client.get(reverse('class_add'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_teacher_can_create_class(self):
        self.client.login(username='teacher_add_class', password='pass12345')
        response = self.client.post(reverse('class_add'), {'name': 'Class Seven'})
        self.assertRedirects(response, reverse('class_list'))
        self.assertTrue(ClassRoom.objects.filter(name='Class Seven').exists())

    def test_duplicate_class_name_rejected(self):
        ClassRoom.objects.create(name='Class Six')
        self.client.login(username='teacher_add_class', password='pass12345')
        response = self.client.post(reverse('class_add'), {'name': 'Class Six'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClassRoom.objects.filter(name='Class Six').count(), 1)


class StudentLoginBlockedTests(TestCase):
    def setUp(self):
        self.room = ClassRoom.objects.create(name='Block Room')
        self.student_user = User.objects.create_user(
            username='stu1',
            password='pass12345',
            role='student',
        )
        Student.objects.create(
            user=self.student_user,
            full_name='Blocked Student',
            school_name='Test School',
            classroom=self.room,
            guardian_phone_1='01700000000',
            is_approved=True,
        )

    def test_student_cannot_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'stu1',
            'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='stu1')
        self.assertNotIn('_auth_user_id', self.client.session)


class TeacherLoginTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teach_login',
            password='pass12345',
            role='teacher',
        )

    def test_teacher_can_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'teach_login',
            'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('home'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_teacher_login_page_is_public(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)


class TeacherAddStudentTests(TestCase):
    def setUp(self):
        self.room = ClassRoom.objects.create(name='Add Room')
        self.teacher = User.objects.create_user(
            username='teacher2',
            password='pass12345',
            role='teacher',
        )
        self.client.login(username='teacher2', password='pass12345')

    def test_teacher_adds_student_as_approved(self):
        response = self.client.post(reverse('add_student'), {
            'full_name':       'New Student',
            'school_name':     'Add School',
            'classroom':       self.room.id,
            'guardian_phone_1': '01800000000',
        })
        self.assertRedirects(
            response,
            reverse('student_list', args=[self.room.id]),
        )
        student = Student.objects.get(full_name='New Student')
        self.assertTrue(student.is_approved)
        self.assertEqual(student.classroom, self.room)

        user = student.user
        self.assertEqual(user.role, 'student')
        self.assertEqual(user.email, '')
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.username, 'new-student-0000')


class StudentListPaginationTests(TestCase):
    def setUp(self):
        self.room = ClassRoom.objects.create(name='Big Room')
        self.teacher = User.objects.create_user(
            username='teach_pag',
            password='pass12345',
            role='teacher',
        )
        self.client.login(username='teach_pag', password='pass12345')
        for i in range(25):
            u = User.objects.create_user(
                username=f'pagstu{i}',
                role='student',
            )
            Student.objects.create(
                user=u,
                full_name=f'Student {i}',
                school_name='School',
                classroom=self.room,
                guardian_phone_1='01700000000',
                is_approved=True,
            )

    def test_student_list_paginates(self):
        response = self.client.get(reverse('student_list', args=[self.room.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj'].object_list), 10)
        self.assertEqual(response.context['total_count'], 25)

        response = self.client.get(
            reverse('student_list', args=[self.room.id]),
            {'page': 2},
        )
        self.assertEqual(len(response.context['page_obj'].object_list), 10)
