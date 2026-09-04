from django.db import models
from django.contrib.auth.models import AbstractUser


class SiteSettings(models.Model):
    academy_name = models.CharField(max_length=200, default="Kornofuli Biggan Academy")
    tagline = models.CharField(max_length=300, default="Pakundia, Kishoreganj — Premier Coaching Center")
    established_year = models.PositiveIntegerField(default=2009)
    hero_heading = models.CharField(max_length=300, default="Build Your Future with")
    hero_subtext = models.TextField(default="Expert coaching for SSC C students.")
    enroll_btn_text = models.CharField(max_length=100, default="Enroll for 2025 Batch")
    enroll_btn_url = models.CharField(max_length=200, default="#")
    phone_primary = models.CharField(max_length=20, blank=True)
    phone_secondary = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True, default="Pakundia, Kishoreganj, Bangladesh")
    office_hours = models.CharField(max_length=200, default="Sat – Thu: 8:00 AM – 9:00 PM | Friday: Closed")
    how_to_reach = models.TextField(blank=True, default="Accessible via CNG, bus route 3 & 7, and rickshaw from GEC Circle")
    google_maps_url = models.URLField(blank=True, default="https://maps.google.com")
    google_maps_embed_url = models.URLField(blank=True, help_text="Google Maps embed iframe src URL")
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    brochure_url = models.CharField(max_length=200, blank=True, default="#")

    # Stats (shown in hero stats bar)
    stat_students = models.CharField(max_length=20, default="3,000+")
    stat_experience = models.CharField(max_length=20, default="15+")
    stat_pass_rate = models.CharField(max_length=20, default="92%")
    stat_teachers = models.CharField(max_length=20, default="25+")

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.academy_name


SUBJECT_CHOICES = [
    ("physics", "Physics"),
    ("chemistry", "Chemistry"),
    ("biology", "Biology"),
    ("mathematics", "Mathematics"),
    ("english", "English"),
    ("ict", "ICT"),
    ("other", "Other"),
]

ICON_CHOICES = [
    ("ti ti-atom", "Atom (Physics)"),
    ("ti ti-flask", "Flask (Chemistry)"),
    ("ti ti-dna", "DNA (Biology)"),
    ("ti ti-math-function", "Math"),
    ("ti ti-book", "Book"),
    ("ti ti-device-laptop", "Laptop (ICT)"),
    ("ti ti-language", "Language"),
    ("ti ti-pencil", "Pencil"),
]

LEVEL_CHOICES = [
    ("six", "SSC"),
    ("seven", "SEVEN"),
    ("eight","EIGHT"),
    ("nine", "NINE"),
    ("ten", "TEN"),

]


class Course(models.Model):
    name = models.CharField(max_length=150)
    subject = models.CharField(max_length=30, choices=SUBJECT_CHOICES, default="other")
    description = models.TextField()
    icon = models.CharField(max_length=60, choices=ICON_CHOICES, default="ti ti-book")
    icon_bg_color = models.CharField(max_length=10, default="#E6F1FB")
    icon_color = models.CharField(max_length=10, default="#0C447C")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="six")
    fee_per_month = models.PositiveIntegerField(null=True, blank=True, help_text="Monthly fee in BDT")
    

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

    @property
    def level_display(self):
        return self.get_level_display().replace(" & ", " · ")

    @property
    def is_full(self):
        schedules = self.schedules.all()
        if not schedules.exists():
            return False
        return all(schedule.is_full for schedule in schedules)


class Teacher(models.Model):
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100, blank=True, help_text="e.g. Senior Lecturer")
    subject = models.CharField(max_length=30, choices=SUBJECT_CHOICES, default="other")
    qualification = models.CharField(max_length=100, help_text="e.g. M.Sc. in Physics")
    experience_years = models.PositiveIntegerField(default=1)
    short_bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="teachers/", null=True, blank=True)
    avatar_initials = models.CharField(max_length=3, blank=True, help_text="Auto-generated if blank")
    avatar_bg = models.CharField(max_length=10, default="#E6F1FB")
    avatar_color = models.CharField(max_length=10, default="#0C447C")
   
    

    class Meta:
        ordering = [ "name"]

    def __str__(self):
        return self.name

    


class Result(models.Model):
    year = models.PositiveIntegerField()
    label = models.CharField(max_length=100, help_text="e.g. HSC Pass Rate")
    value = models.CharField(max_length=20, help_text="e.g. 98% or 340")
    tag = models.CharField(max_length=50, help_text="e.g. 2024 Board")
    tag_bg = models.CharField(max_length=10, default="#EAF3DE")
    tag_color = models.CharField(max_length=10, default="#27500A")
    order = models.PositiveIntegerField(default=0)
   

    class Meta:
        ordering = ["-year", "order"]

    def __str__(self):
        return f"{self.year} — {self.label}: {self.value}"


NOTICE_TYPE_CHOICES = [
    ("info", "Info"),
    ("warning", "Warning"),
    ("success", "Success"),
    ("urgent", "Urgent"),
]


class Notice(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    notice_type = models.CharField(max_length=20, choices=NOTICE_TYPE_CHOICES, default="info")
    is_pinned = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="notices/", null=True, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)
   
    
 

    class Meta:
        ordering = ["-is_pinned", "-published_at"]

    def __str__(self):
        return self.title

    @property
    def type_icon(self):
        icons = {
            "info": "ti ti-info-circle",
            "warning": "ti ti-alert-triangle",
            "success": "ti ti-circle-check",
            "urgent": "ti ti-bell-ringing",
        }
        return icons.get(self.notice_type, "ti ti-info-circle")

    @property
    def type_color(self):
        colors = {
            "info": "#0C447C",
            "warning": "#92400E",
            "success": "#166534",
            "urgent": "#991B1B",
        }
        return colors.get(self.notice_type, "#0C447C")

    @property
    def type_bg(self):
        bgs = {
            "info": "#E6F1FB",
            "warning": "#FEF3C7",
            "success": "#DCFCE7",
            "urgent": "#FEE2E2",
        }
        return bgs.get(self.notice_type, "#E6F1FB")




class GalleryImage(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=300, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
   
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-uploaded_at"]

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    

    class Meta:
        ordering = ["order"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class BatchSchedule(models.Model):
    DAY_CHOICES = [
        ("sat_thu", "Sat – Thu"),
        ("sat_wed", "Sat – Wed"),
        ("fri_sat", "Fri – Sat"),
        ("daily", "Daily"),
    ]
    TIME_CHOICES = [
        ("morning", "Morning"),
        ("afternoon", "Afternoon"),
        ("evening", "Evening"),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="schedules")
    batch_name = models.CharField(max_length=100, help_text="e.g. SSC Morning Batch A")
    days = models.CharField(max_length=20, choices=DAY_CHOICES, default="sat_thu")
    time_slot = models.CharField(max_length=20, choices=TIME_CHOICES, default="morning")
    start_time = models.TimeField()
    end_time = models.TimeField()
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="batches")
    seats_total = models.PositiveIntegerField(default=25)
    seats_enrolled = models.PositiveIntegerField(default=0)
    

    class Meta:
        ordering = ["time_slot", "batch_name"]

    def __str__(self):
        return f"{self.batch_name} — {self.course.name}"

    @property
    def seats_left(self):
        return self.seats_total - self.seats_enrolled

    @property
    def is_full(self):
        return self.seats_left <= 0
