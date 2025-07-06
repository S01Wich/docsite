import re
import os
from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.http import FileResponse
from django.conf import settings

from docx import Document
from docx.oxml.ns import qn

from .models import TemplateDoc
from .forms import generate_template_form

# Паттерн: только {$Тег}, без учёта стилей внутри
TAG_PATTERN = r'\{\$(?P<tag>[A-Za-zА-Яа-я0-9_]+)\}'

def index(request):
    templates = TemplateDoc.objects.all()
    return render(request, 'index.html', {'templates': templates})

def fill_template(request, pk):
    template = get_object_or_404(TemplateDoc, pk=pk)
    doc_path = template.doc_file.path

    # Загружаем документ и собираем все теги {$...}
    doc = Document(doc_path)
    tags = set()
    for p in doc.paragraphs:
        for m in re.finditer(TAG_PATTERN, p.text):
            tags.add(m.group('tag'))
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for m in re.finditer(TAG_PATTERN, p.text):
                        tags.add(m.group('tag'))

    # Сортировка: сначала по отсутствию цифр, затем по числовой части и по алфавиту
    def sort_key(tag):
        m = re.match(r"(.+?)(\d+)$", tag)
        if m:
            return (int(m.group(2)), m.group(1).lower())
        return (0, tag.lower())
    sorted_tags = sorted(tags, key=sort_key)

    TemplateForm = generate_template_form(sorted_tags)

    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            # Создаём копию документа для правок
            output_doc = Document(doc_path)

            # Встроенная замена в каждом run, чтобы не трогать bold/italic и пр.
            for paragraph in output_doc.paragraphs:
                for run in paragraph.runs:
                    if re.search(TAG_PATTERN, run.text):
                        run.text = re.sub(
                            TAG_PATTERN,
                            lambda m: str(form.cleaned_data.get(m.group('tag'), '')),
                            run.text
                        )
                    # Обновляем шрифт, не затрагивая остальные атрибуты
                    run.font.name = 'Times New Roman'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

            for table in output_doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                if re.search(TAG_PATTERN, run.text):
                                    run.text = re.sub(
                                        TAG_PATTERN,
                                        lambda m: str(form.cleaned_data.get(m.group('tag'), '')),
                                        run.text
                                    )
                                run.font.name = 'Times New Roman'
                                run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

            # Формируем имя файла: <оригинал>_<YYYY-MM-DD>.docx
            basename = os.path.basename(doc_path)
            name, ext = os.path.splitext(basename)
            if not ext:
                ext = '.docx'
            date_str = datetime.now().strftime('%Y-%m-%d')
            output_filename = f"{name}_{date_str}{ext}"

            # Сохраняем в MEDIA_ROOT и возвращаем
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            output_path = os.path.join(settings.MEDIA_ROOT, output_filename)
            output_doc.save(output_path)

            return FileResponse(
                open(output_path, 'rb'),
                as_attachment=True,
                filename=output_filename
            )
    else:
        form = TemplateForm()

    return render(request, 'fill_template.html', {
        'template': template,
        'form': form,
    })
