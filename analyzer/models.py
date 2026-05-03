from django.db import models


class ResumeRecord(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    # File / Candidate Info
    filename = models.CharField(max_length=255, blank=True, null=True)
    target_role = models.CharField(max_length=150, blank=True, null=True)

    # Analysis Data
    skills = models.TextField()
    score = models.IntegerField()
    match_score = models.IntegerField(default=0)

    summary = models.TextField()
    jobs = models.TextField()

    # Full AI Report
    ai_report = models.TextField(blank=True, null=True)

    def __str__(self):
        role = self.target_role if self.target_role else "General"
        return f"Resume {self.id} - {role} - {self.score}%"