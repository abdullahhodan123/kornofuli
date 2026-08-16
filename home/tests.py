from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Course, SiteSettings


class ManageWebsiteAuthorizationTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teach_manage',
            password='pass12345',
            role='teacher',
        )
        self.student = User.objects.create_user(
            username='stu_manage',
            password='pass12345',
            role='student',
        )

    def test_manage_page_requires_login(self):
        response = self.client.get(reverse('manage_content', args=['course']))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_manage_page_blocks_student(self):
        self.client.login(username='stu_manage', password='pass12345')
        response = self.client.get(reverse('manage_content', args=['course']))
        self.assertRedirects(response, reverse('home'))

    def test_teacher_can_open_manage_page(self):
        self.client.login(username='teach_manage', password='pass12345')
        response = self.client.get(reverse('manage_content', args=['course']))
        self.assertEqual(response.status_code, 200)


class ManageContentTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teach_content',
            password='pass12345',
            role='teacher',
        )
        self.client.login(username='teach_content', password='pass12345')

    def test_teacher_creates_course(self):
        response = self.client.post(reverse('manage_content', args=['course']), {
            'name':        'Physics Special',
            'subject':     'physics',
            'description': 'Full syllabus coaching',
            'icon':        'ti ti-atom',
            'icon_bg_color': '#E6F1FB',
            'icon_color':  '#0C447C',
            'level':       'ten',
            'fee_per_month': 1500,
            'order':       1,
        })
        self.assertRedirects(response, reverse('manage_content', args=['course']))
        self.assertTrue(Course.objects.filter(name='Physics Special').exists())

    def test_teacher_edits_course(self):
        course = Course.objects.create(
            name='Old Name',
            subject='physics',
            description='Desc',
        )
        response = self.client.post(
            reverse('manage_edit', args=['course', course.pk]),
            {
                'name':        'New Name',
                'subject':     'chemistry',
                'description': 'Updated',
                'icon':        'ti ti-flask',
                'icon_bg_color': '#E6F1FB',
                'icon_color':  '#0C447C',
                'level':       'nine',
                'order':       0,
            },
        )
        self.assertRedirects(response, reverse('manage_content', args=['course']))
        course.refresh_from_db()
        self.assertEqual(course.name, 'New Name')
        self.assertEqual(course.subject, 'chemistry')

    def test_teacher_deletes_course(self):
        course = Course.objects.create(
            name='To Delete',
            subject='physics',
            description='Desc',
        )
        response = self.client.post(reverse('manage_delete', args=['course', course.pk]))
        self.assertRedirects(response, reverse('manage_content', args=['course']))
        self.assertFalse(Course.objects.filter(pk=course.pk).exists())

    def test_invalid_model_key_redirects_home(self):
        response = self.client.get(reverse('manage_content', args=['nonsense']))
        self.assertRedirects(response, reverse('home'))

    def test_manage_content_paginates(self):
        for i in range(20):
            Course.objects.create(
                name=f'Course {i}',
                subject='physics',
                description='Desc',
            )
        response = self.client.get(reverse('manage_content', args=['course']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.num_pages, 4)
        self.assertEqual(len(response.context['page_obj'].object_list), 5)
        self.assertContains(response, 'm-pagination')

        response = self.client.get(reverse('manage_content', args=['course']), {'page': 2})
        self.assertEqual(len(response.context['page_obj'].object_list), 5)
        self.assertContains(response, 'm-pagination')


class ManageSettingsTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teach_settings',
            password='pass12345',
            role='teacher',
        )
        self.client.login(username='teach_settings', password='pass12345')

    def test_teacher_updates_site_settings(self):
        settings, _ = SiteSettings.objects.get_or_create()
        response = self.client.post(reverse('manage_settings'), {
            'academy_name':       'New Academy',
            'tagline':            'Tagline',
            'established_year':   '2010',
            'hero_heading':       'Heading',
            'hero_subtext':       'Subtext',
            'enroll_btn_text':    'Enroll',
            'enroll_btn_url':     '#',
            'phone_primary':      '01700000000',
            'phone_secondary':    '',
            'whatsapp_number':    '',
            'email':              'info@example.com',
            'address':            'Address',
            'office_hours':       'Hours',
            'how_to_reach':       'Reach',
            'google_maps_url':    'https://maps.google.com',
            'google_maps_embed_url': '',
            'facebook_url':       '',
            'youtube_url':        '',
            'brochure_url':       '#',
            'stat_students':      '4,000+',
            'stat_experience':    '16+',
            'stat_pass_rate':     '95%',
            'stat_teachers':      '30+',
        })
        self.assertRedirects(response, reverse('home'))
        settings.refresh_from_db()
        self.assertEqual(settings.academy_name, 'New Academy')
