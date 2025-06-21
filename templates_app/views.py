import re
import os
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from .models import TemplateDoc
from .forms import generate_template_form
from docx import Document

# Пространство имён для WordprocessingML
WORD_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# Паттерн для тегов: захватываем имя тега до ':' или '}'
TAG_PATTERN = r'{\$(?P<tag>[^}:]+)(?::[bi])?}'

# Импорт для рекурсии по таблицам и ячейкам
from docx.document import Document as _Document
from docx.table import _Cell, Table

def iter_paragraphs(element):
    if isinstance(element, _Document) or isinstance(element, _Cell):
        for paragraph in element.paragraphs:
            yield paragraph
        for table in getattr(element, 'tables', []):
            for row in table.rows:
                for cell in row.cells:
                    yield from iter_paragraphs(cell)
    elif isinstance(element, Table):
        for row in element.rows:
            for cell in row.cells:
                yield from iter_paragraphs(cell)

# Главная страница

def index(request):
    templates = TemplateDoc.objects.all()
    return render(request, 'index.html', {'templates': templates})

# Страница заполнения шаблона
def fill_template(request, pk):
    template = get_object_or_404(TemplateDoc, pk=pk)
    doc_path = template.doc_file.path
    doc = Document(doc_path)

    # Собираем теги из параграфов и таблиц
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

    # Сортировка: сначала теги без числа (группа 0) в алфавитном порядке,
    # затем группы 1,2,... по возрастанию, внутри каждой — тоже в алфавите.
    def sort_key(tag):
        m = re.match(r"(.+?)(\d+)$", tag)
        if m:
            base = m.group(1).lower()
            num = int(m.group(2))
            return (num, base)
        else:
            return (0, tag.lower())

    sorted_tags = sorted(tags, key=sort_key)

    TemplateForm = generate_template_form(sorted_tags)

    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            output_doc = Document(doc_path)
            # Собираем элементы для замены
            elements = list(output_doc.paragraphs)
            for table in output_doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        elements.extend(cell.paragraphs)

            # Заменяем теги на введённые значения
            for p in elements:
                full_text = ''.join(run.text for run in p.runs)
                for tag in sorted_tags:
                    for style in ['', ':b', ':i']:
                        placeholder = '{$' + tag + style + '}'
                        if placeholder in full_text:
                            full_text = full_text.replace(placeholder, form.cleaned_data[tag])
                if full_text != ''.join(run.text for run in p.runs):
                    for run in p.runs:
                        run.text = ''
                    if p.runs:
                        r = p.runs[0]
                        r.text = full_text
                        # Устанавливаем шрифт Times New Roman
                        r.font.name = 'Times New Roman'
                        r._element.rPr.rFonts.set(f'{{{WORD_NS}}}eastAsia', 'Times New Roman')

            # Сохраняем файл и отдаем ответ
            output_filename = f'generated_{template.id}.docx'
            output_path = os.path.join(settings.MEDIA_ROOT, output_filename)
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            output_doc.save(output_path)
            with open(output_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
                return response
    else:
        form = TemplateForm()

    return render(request, 'fill_template.html', {'template': template, 'form': form})