from django.db import models

class TemplateDoc(models.Model):
    name = models.CharField(max_length=255)
    doc_file = models.FileField(upload_to='templates_docs/')

    def __str__(self):
        return self.name